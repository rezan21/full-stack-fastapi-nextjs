import { expect, type Page } from "@playwright/test"
import { SESSION_COOKIE } from "../../src/lib/config"
import { emailedToken, waitForEmailHtml } from "./mailpit"

// Signs up a user through the UI with the emailed link.
export async function signUpNewUser(
  page: Page,
  name: string,
  email: string,
  password: string,
) {
  await page.goto("/signup")

  await page.getByTestId("full-name-input").fill(name)
  await page.getByTestId("email-input").fill(email)
  await page.getByRole("button", { name: "Sign Up" }).click()
  await page.waitForURL("/signup/sent")

  const html = await waitForEmailHtml({
    request: page.context().request,
    query: `to:${email}`,
  })
  await page.goto(`/signup/complete?token=${emailedToken(html)}`)
  await page.getByTestId("new-password-input").fill(password)
  await page.getByTestId("confirm-password-input").fill(password)
  await page.getByRole("button", { name: "Create Account" }).click()
  await page.waitForURL("/login")
}

// Logs a user in through the UI.
export async function logInUser(page: Page, email: string, password: string) {
  await page.goto("/login")

  await page.getByTestId("email-input").fill(email)
  await page.getByTestId("password-input").fill(password)
  await page.getByRole("button", { name: "Log In" }).click()
  await page.waitForURL("/dashboard")
  await expect(
    page.getByText("Welcome back, nice to see you again!"),
  ).toBeVisible()
}

// Logs the current user out through the UI.
export async function logOutUser(page: Page) {
  await page.getByTestId("user-menu").click()
  await page.getByRole("menuitem", { name: "Log out" }).click()
  await page.goto("/login")
}

// Returns the session token from the browser.
export async function sessionToken(page: Page) {
  const cookies = await page.context().cookies()
  return cookies.find((cookie) => cookie.name === SESSION_COOKIE)
    ?.value as string
}
