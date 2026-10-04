import { expect, test } from "@playwright/test"

const pages = ["/", "/dashboard", "/items", "/settings", "/showcase"]

test("Responses carry the security headers", async ({ request }) => {
  const response = await request.get("/login")
  const headers = response.headers()

  expect(headers["content-security-policy"]).toContain("frame-ancestors 'none'")
  expect(headers["content-security-policy"]).toMatch(/script-src [^;]*'nonce-/)
  expect(headers["x-content-type-options"]).toBe("nosniff")
  expect(headers["referrer-policy"]).toBe("strict-origin-when-cross-origin")
  expect(headers["permissions-policy"]).toContain("camera=()")
  expect(headers["x-powered-by"]).toBeUndefined()
})

test("Pages load without Content Security Policy violations", async ({
  page,
}) => {
  const violations: string[] = []
  await page.exposeFunction("reportViolation", (violation: string) =>
    violations.push(violation),
  )
  await page.addInitScript(() => {
    document.addEventListener("securitypolicyviolation", (event) => {
      const report = window as unknown as {
        reportViolation: (violation: string) => void
      }
      report.reportViolation(`${event.violatedDirective} ${event.blockedURI}`)
    })
  })

  for (const path of pages) {
    await page.goto(path)
    await page.waitForLoadState("networkidle")
  }

  expect(violations).toEqual([])
})
