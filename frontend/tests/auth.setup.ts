import { type Page, test as setup } from "@playwright/test"
import { e2eAdminEmail, e2ePassword, e2eUserEmail } from "./config"

async function logIn(page: Page, email: string) {
  await page.goto("/login")
  await page.getByTestId("email-input").fill(email)
  await page.getByTestId("password-input").fill(e2ePassword)
  await page.getByRole("button", { name: "Log In" }).click()
  await page.waitForURL("/dashboard")
}

setup("authenticate the e2e user", async ({ page }) => {
  await logIn(page, e2eUserEmail)
  await page.context().storageState({ path: "playwright/.auth/user.json" })
})

setup("authenticate the e2e admin", async ({ page }) => {
  await logIn(page, e2eAdminEmail)
  await page.context().storageState({ path: "playwright/.auth/admin.json" })
})
