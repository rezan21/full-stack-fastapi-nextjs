import { describe, expect, test } from "bun:test"
import { contentSecurityPolicy } from "@/lib/csp"

const scriptSources = (policy: string) =>
  policy.split("; ").find((part) => part.startsWith("script-src ")) ?? ""

describe("contentSecurityPolicy", () => {
  test("puts the given script sources in the script directive", () => {
    const policy = contentSecurityPolicy("'self' 'nonce-abc'")
    expect(scriptSources(policy)).toBe("script-src 'self' 'nonce-abc'")
  })

  test("allows inline scripts only when asked", () => {
    expect(scriptSources(contentSecurityPolicy("'self'"))).not.toContain(
      "unsafe-inline",
    )
    expect(
      scriptSources(contentSecurityPolicy("'self' 'unsafe-inline'")),
    ).toContain("'unsafe-inline'")
  })

  test("forbids framing, plugins and a rewritten base URL either way", () => {
    for (const sources of ["'self' 'nonce-abc'", "'self' 'unsafe-inline'"]) {
      const policy = contentSecurityPolicy(sources)
      expect(policy).toContain("frame-ancestors 'none'")
      expect(policy).toContain("object-src 'none'")
      expect(policy).toContain("base-uri 'self'")
    }
  })
})
