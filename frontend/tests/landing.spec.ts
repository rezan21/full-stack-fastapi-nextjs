import { expect, test } from "@playwright/test"

test.describe("signed out", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("The landing page offers the login", async ({ page }) => {
    await page.goto("/")

    await expect(page.getByRole("heading", { level: 1 })).toBeVisible()
    await page.getByRole("button", { name: "Log in" }).click()

    await expect(page).toHaveURL(/\/login$/)
  })
})

test("A signed-in visitor who follows the login lands on the dashboard", async ({
  page,
}) => {
  await page.goto("/")
  await page.getByRole("button", { name: "Log in" }).click()

  await expect(page).toHaveURL(/\/dashboard$/)
})
