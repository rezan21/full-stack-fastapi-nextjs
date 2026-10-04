import { expect, test } from "@playwright/test"

test.describe("signed out", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("The landing page offers the login", async ({ page }) => {
    await page.goto("/")

    await expect(page.getByRole("heading", { level: 1 })).toBeVisible()
    await expect(page.getByRole("button", { name: "Dashboard" })).toHaveCount(0)
    await page.getByRole("button", { name: "Log in" }).click()

    await expect(page).toHaveURL(/\/login$/)
  })
})

test("The landing page offers the dashboard to a signed-in user", async ({
  page,
}) => {
  await page.goto("/")

  await expect(page.getByRole("button", { name: "Log in" })).toHaveCount(0)
  await page.getByRole("button", { name: "Dashboard" }).click()

  await expect(page).toHaveURL(/\/dashboard$/)
})
