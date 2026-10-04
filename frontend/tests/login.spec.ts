import { expect, type Page, test } from "@playwright/test"
import { SESSION_COOKIE } from "../src/lib/config"
import { firstSuperuser, firstSuperuserPassword } from "./config"
import { createUser } from "./utils/api"
import { randomEmail, randomPassword } from "./utils/random"

test.use({ storageState: { cookies: [], origins: [] } })

const fillForm = async (page: Page, email: string, password: string) => {
  await page.getByTestId("email-input").fill(email)
  await page.getByTestId("password-input").fill(password)
}

const verifyInput = async (page: Page, testId: string) => {
  const input = page.getByTestId(testId)
  await expect(input).toBeVisible()
  await expect(input).toHaveText("")
  await expect(input).toBeEditable()
}

test("Inputs are visible, empty and editable", async ({ page }) => {
  await page.goto("/login")

  await verifyInput(page, "email-input")
  await verifyInput(page, "password-input")
})

test("Log In button is visible", async ({ page }) => {
  await page.goto("/login")

  await expect(page.getByRole("button", { name: "Log In" })).toBeVisible()
})

test("Forgot Password link is visible", async ({ page }) => {
  await page.goto("/login")

  await expect(
    page.getByRole("link", { name: "Forgot your password?" }),
  ).toBeVisible()
})

test("Log in with valid email and password ", async ({ page }) => {
  await page.goto("/login")

  await fillForm(page, firstSuperuser, firstSuperuserPassword)
  await page.getByRole("button", { name: "Log In" }).click()

  await page.waitForURL("/dashboard")

  await expect(
    page.getByText("Welcome back, nice to see you again!"),
  ).toBeVisible()
})

test("Log in with invalid email", async ({ page }) => {
  await page.goto("/login")

  await fillForm(page, "invalidemail", firstSuperuserPassword)
  await page.getByRole("button", { name: "Log In" }).click()

  await expect(page.getByText("Invalid email")).toBeVisible()
})

test("Log in with invalid password", async ({ page }) => {
  const email = randomEmail()
  await createUser({ email, password: randomPassword() })

  await page.goto("/login")
  await fillForm(page, email, randomPassword())
  await page.getByRole("button", { name: "Log In" }).click()

  await expect(page.getByText("Incorrect email or password")).toBeVisible()
})

test("Repeated wrong passwords lock the account for a while", async ({
  page,
}) => {
  const email = randomEmail()
  const password = randomPassword()
  await createUser({ email, password })
  const submit = async (attempt: string) => {
    await fillForm(page, email, attempt)
    await Promise.all([
      page.waitForResponse(
        (response) =>
          response.request().method() === "POST" &&
          new URL(response.url()).pathname === "/login",
      ),
      page.getByRole("button", { name: "Log In" }).click(),
    ])
  }

  await page.goto("/login")
  for (let wrong = 0; wrong < 5; wrong++) await submit(randomPassword())
  await submit(password)

  await expect(page.getByText(/Too many failed attempts/)).toBeVisible()
  await expect(page).toHaveURL(/\/login$/)
})

test("Successful log out", async ({ page }) => {
  const email = randomEmail()
  const password = randomPassword()
  await createUser({ email, password })
  await page.goto("/login")

  await fillForm(page, email, password)
  await page.getByRole("button", { name: "Log In" }).click()

  await page.waitForURL("/dashboard")

  await expect(
    page.getByText("Welcome back, nice to see you again!"),
  ).toBeVisible()

  await page.getByTestId("user-menu").click()
  await page.getByRole("menuitem", { name: "Log out" }).click()
  await page.waitForURL("/login")
})

test("Logged-out user cannot access protected routes", async ({ page }) => {
  const email = randomEmail()
  const password = randomPassword()
  await createUser({ email, password })
  await page.goto("/login")

  await fillForm(page, email, password)
  await page.getByRole("button", { name: "Log In" }).click()

  await page.waitForURL("/dashboard")

  await expect(
    page.getByText("Welcome back, nice to see you again!"),
  ).toBeVisible()

  await page.getByTestId("user-menu").click()
  await page.getByRole("menuitem", { name: "Log out" }).click()
  await page.waitForURL("/login")

  await page.goto("/settings")
  await page.waitForURL("/login")
})

test("Sends a logged-out visitor to /login from a path that does not exist", async ({
  page,
}) => {
  await page.goto("/no-such-page")
  await expect(page).toHaveURL("/login")
})

test("Redirects to /login from the items page when token is wrong", async ({
  page,
  context,
  baseURL,
}) => {
  await context.addCookies([
    { name: SESSION_COOKIE, value: "invalid_token", url: baseURL as string },
  ])
  await page.goto("/items")
  await expect(page).toHaveURL("/login")
})

test("Redirects to /login when token is wrong", async ({
  page,
  context,
  baseURL,
}) => {
  await context.addCookies([
    { name: SESSION_COOKIE, value: "invalid_token", url: baseURL as string },
  ])
  await page.goto("/settings")
  await page.waitForURL("/login")
  await expect(page).toHaveURL("/login")
})
