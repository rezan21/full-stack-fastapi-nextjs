import { describe, expect, test } from "bun:test"
import { readdirSync, statSync } from "node:fs"
import { join } from "node:path"
import { NextRequest } from "next/server"
import { CHAT_RUN_URL, SESSION_COOKIE } from "@/lib/config"
import { config, proxy } from "@/proxy"

const ORIGIN = "http://localhost:3000"
const AUTH_DIR = join(import.meta.dir, "app", "(product)", "(auth)")

function visit(path: string, session?: string) {
  const headers: Record<string, string> = session
    ? { cookie: `${SESSION_COOKIE}=${session}` }
    : {}
  return proxy(new NextRequest(`${ORIGIN}${path}`, { headers }))
}

const passesThrough = (response: Response) =>
  response.headers.get("x-middleware-next") === "1"

function routesIn(dir: string, base = ""): string[] {
  return readdirSync(dir).flatMap((name) => {
    if (!statSync(join(dir, name)).isDirectory()) return []
    const route = `${base}/${name}`
    return [route, ...routesIn(join(dir, name), route)]
  })
}

const publicRoutes = [...routesIn(AUTH_DIR), "/confirm-email"]

const covered = (path: string) =>
  new RegExp(`^${config.matcher[0]}$`).test(path)

describe("proxy", () => {
  test("leaves the cached landing page and static files alone", () => {
    for (const path of ["/", "/_next/static/chunk.js", "/api/x"]) {
      expect(covered(path), path).toBe(false)
    }
    for (const path of ["/login", "/dashboard", "/no-such-page"]) {
      expect(covered(path), path).toBe(true)
    }
  })

  test("leaves the chat stream to its own session check, and nothing else under it", () => {
    expect(covered(CHAT_RUN_URL)).toBe(false)
    for (const path of ["/chat", "/chat/abc", `${CHAT_RUN_URL}-history`]) {
      expect(covered(path), path).toBe(true)
    }
  })

  test("lets every page of the (auth) route group through without a session", () => {
    expect(publicRoutes.length).toBeGreaterThan(0)
    for (const path of publicRoutes) {
      expect(passesThrough(visit(path))).toBe(true)
    }
  })

  test("sends a visitor without a session to /login from any other path", () => {
    for (const path of [
      "/dashboard",
      "/items",
      "/items/abc",
      "/settings",
      "/unknown",
    ]) {
      const response = visit(path)
      expect(response.status).toBe(307)
      expect(response.headers.get("location")).toBe(`${ORIGIN}/login`)
    }
  })

  test("lets a visitor with a session cookie through everywhere", () => {
    for (const path of ["/dashboard", "/items", "/settings", ...publicRoutes]) {
      expect(passesThrough(visit(path, "any-token"))).toBe(true)
    }
  })
})

const policyOf = (path: string) =>
  visit(path).headers.get("content-security-policy") ?? ""

const directive = (policy: string, name: string) =>
  policy.split("; ").find((part) => part.startsWith(`${name} `)) ?? ""

describe("content security policy", () => {
  test("allows only scripts that carry the nonce of that response", () => {
    const script = directive(policyOf("/login"), "script-src")
    expect(script).toMatch(/^script-src 'self' 'nonce-[^']+' 'strict-dynamic'$/)
  })

  test("uses a new nonce for every response", () => {
    expect(policyOf("/login")).not.toBe(policyOf("/login"))
  })

  test("hands the same nonce to the app through the request", () => {
    const response = visit("/login")
    const policy = response.headers.get("content-security-policy") ?? ""
    const nonce = response.headers.get("x-middleware-request-x-nonce")
    expect(nonce).toBeTruthy()
    expect(policy).toContain(`'nonce-${nonce}'`)
  })

  test("forbids framing, plugins and a rewritten base URL", () => {
    const policy = policyOf("/login")
    expect(policy).toContain("frame-ancestors 'none'")
    expect(policy).toContain("object-src 'none'")
    expect(policy).toContain("base-uri 'self'")
    expect(policy).toContain("form-action 'self'")
  })

  test("allows eval only in development", () => {
    expect(directive(policyOf("/login"), "script-src")).not.toContain("eval")
    const env = process.env as Record<string, string | undefined>
    const original = env.NODE_ENV
    env.NODE_ENV = "development"
    try {
      expect(directive(policyOf("/login"), "script-src")).toContain(
        "'unsafe-eval'",
      )
    } finally {
      env.NODE_ENV = original
    }
  })

  test("is set for a visitor with a session as well", () => {
    expect(
      visit("/", "any-token").headers.get("content-security-policy"),
    ).toContain("script-src")
  })
})
