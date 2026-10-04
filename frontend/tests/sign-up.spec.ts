import { expect, type Page, test } from "@playwright/test"
import { emailedToken, waitForEmailHtml } from "./utils/mailpit"
import { randomEmail, randomPassword } from "./utils/random"
import { logInUser, signUpNewUser } from "./utils/user"

test.use({ storageState: { cookies: [], origins: [] } })

const fillForm = async (page: Page, full_name: string, email: string) => {
  await page.getByTestId("full-name-input").fill(full_name)
  await page.getByTestId("email-input").fill(email)
}

const verifyInput = async (page: Page, testId: string) => {
  const input = page.getByTestId(testId)
  await expect(input).toBeVisible()
  await expect(input).toHaveText("")
  await expect(input).toBeEditable()
}

const requestLink = async (page: Page, email: string) => {
  await page.goto("/signup")
  await fillForm(page, "Test User", email)
  await page.getByRole("button", { name: "Sign Up" }).click()
  await page.waitForURL("/signup/sent")

  const html = await waitForEmailHtml({
    request: page.context().request,
    query: `to:${email}`,
  })
  return `/signup/complete?token=${emailedToken(html)}`
}

const setPassword = async (
  page: Page,
  password: string,
  confirm_password = password,
) => {
  await page.getByTestId("new-password-input").fill(password)
  await page.getByTestId("confirm-password-input").fill(confirm_password)
  await page.getByRole("button", { name: "Create Account" }).click()
}

test("Inputs are visible, empty and editable", async ({ page }) => {
  await page.goto("/signup")

  await verifyInput(page, "full-name-input")
  await verifyInput(page, "email-input")
  await expect(page.getByTestId("password-input")).toHaveCount(0)
})

test("Sign Up button is visible", async ({ page }) => {
  await page.goto("/signup")

  await expect(page.getByRole("button", { name: "Sign Up" })).toBeVisible()
})

test("Log In link is visible", async ({ page }) => {
  await page.goto("/signup")

  await expect(page.getByRole("link", { name: "Log In" })).toBeVisible()
})

test("Sign up with a valid name and email asks to check the email", async ({
  page,
}) => {
  await page.goto("/signup")
  await fillForm(page, "Test User", randomEmail())
  await page.getByRole("button", { name: "Sign Up" }).click()

  await expect(page).toHaveURL("/signup/sent")
  await expect(
    page.getByText("If that email can be used to sign up"),
  ).toBeVisible()
})

test("Sign up with invalid email", async ({ page }) => {
  await page.goto("/signup")

  await fillForm(page, "Playwright Test", "invalid-email")
  await page.getByRole("button", { name: "Sign Up" }).click()

  await expect(page.getByText("Invalid email")).toBeVisible()
})

test("Sign up with an existing email looks the same", async ({ page }) => {
  const email = randomEmail()
  await signUpNewUser(page, "Test User", email, randomPassword())

  await page.goto("/signup")
  await fillForm(page, "Test User", email)
  await page.getByRole("button", { name: "Sign Up" }).click()

  await expect(page).toHaveURL("/signup/sent")
  await expect(
    page.getByText("If that email can be used to sign up"),
  ).toBeVisible()
})

test("Sign up with missing full name", async ({ page }) => {
  await page.goto("/signup")

  await fillForm(page, "", randomEmail())
  await page.getByRole("button", { name: "Sign Up" }).click()

  await expect(page.getByText("Full Name is required")).toBeVisible()
})

test("Sign up with missing email", async ({ page }) => {
  await page.goto("/signup")

  await fillForm(page, "Test User", "")
  await page.getByRole("button", { name: "Sign Up" }).click()

  await expect(page.getByText("Invalid email")).toBeVisible()
})

test("The emailed link creates an account that can log in", async ({
  page,
}) => {
  const email = randomEmail()
  const password = randomPassword()

  await signUpNewUser(page, "Test User", email, password)

  await logInUser(page, email, password)
})

test("The sign-up link works once", async ({ page }) => {
  const email = randomEmail()
  const link = await requestLink(page, email)

  await page.goto(link)
  await setPassword(page, randomPassword())
  await page.waitForURL("/login")

  await page.goto(link)
  await setPassword(page, randomPassword())

  await expect(page.getByText("Invalid token")).toBeVisible()
})

test("Completing sign-up with a weak password", async ({ page }) => {
  await page.goto(await requestLink(page, randomEmail()))

  await setPassword(page, "weak")

  await expect(
    page.getByText("Password must be at least 8 characters"),
  ).toBeVisible()
})

test("Completing sign-up with mismatched passwords", async ({ page }) => {
  await page.goto(await requestLink(page, randomEmail()))

  await setPassword(page, randomPassword(), randomPassword())

  await expect(page.getByText("The passwords don't match")).toBeVisible()
})

test("The sign-up page without a token goes to login", async ({ page }) => {
  await page.goto("/signup/complete")

  await expect(page).toHaveURL(/\/login$/)
})
