import { describe, expect, test } from "bun:test"
import { readdirSync, statSync } from "node:fs"
import { join } from "node:path"
import { NextRequest } from "next/server"
import { SESSION_COOKIE } from "@/lib/config"
import { proxy } from "@/proxy"

const ORIGIN = "http://localhost:3000"
const AUTH_DIR = join(import.meta.dir, "app", "(auth)")

function visit(path: string, session?: string) {
  const headers: Record<string, string> = session
    ? { cookie: `${SESSION_COOKIE}=${session}` }
    : {}
  return proxy(new NextRequest(`${ORIGIN}${path}`, { headers }))
}

const passesThrough = (response: Response) =>
  response.headers.get("x-middleware-next") === "1"

const publicRoutes = readdirSync(AUTH_DIR)
  .filter((name) => statSync(join(AUTH_DIR, name)).isDirectory())
  .map((name) => `/${name}`)

describe("proxy", () => {
  test("lets every page of the (auth) route group through without a session", () => {
    expect(publicRoutes.length).toBeGreaterThan(0)
    for (const path of publicRoutes) {
      expect(passesThrough(visit(path))).toBe(true)
    }
  })

  test("sends a visitor without a session to /login from any other path", () => {
    for (const path of ["/", "/items", "/items/abc", "/settings", "/unknown"]) {
      const response = visit(path)
      expect(response.status).toBe(307)
      expect(response.headers.get("location")).toBe(`${ORIGIN}/login`)
    }
  })

  test("lets a visitor with a session cookie through everywhere", () => {
    for (const path of ["/", "/items", "/settings", ...publicRoutes]) {
      expect(passesThrough(visit(path, "any-token"))).toBe(true)
    }
  })
})
