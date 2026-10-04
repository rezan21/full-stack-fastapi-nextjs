import { expect, type Page, test } from "@playwright/test"
import { firstSuperuserPassword } from "./config"
import { createUser } from "./utils/api"
import { emailedToken, waitForEmailHtml } from "./utils/mailpit"
import { randomEmail, randomPassword } from "./utils/random"
import { typeInto } from "./utils/type"
import { logInUser, logOutUser } from "./utils/user"

const tabs = ["My profile", "Password", "Danger zone"]

async function openAppearanceMenu(page: Page) {
  await page.getByTestId("user-menu").click()
  await page.getByTestId("theme-button").click()
}

test("Settings is reachable from the user menu", async ({ page }) => {
  await page.goto("/")
  await page.getByTestId("user-menu").click()
  await page.getByRole("menuitem", { name: "Settings" }).click()

  await expect(page).toHaveURL(/\/settings$/)
  await expect(page.getByRole("tab", { name: "My profile" })).toBeVisible()
})

test("My profile tab is active by default", async ({ page }) => {
  await page.goto("/settings")
  await expect(page.getByRole("tab", { name: "My profile" })).toHaveAttribute(
    "aria-selected",
    "true",
  )
})

test("All tabs are visible", async ({ page }) => {
  await page.goto("/settings")
  for (const tab of tabs) {
    await expect(page.getByRole("tab", { name: tab })).toBeVisible()
  }
})

test.describe("Edit user profile", () => {
  test.use({ storageState: { cookies: [], origins: [] } })
  let email: string
  let password: string

  test.beforeAll(async () => {
    email = randomEmail()
    password = randomPassword()
    await createUser({ email, password })
  })

  test.beforeEach(async ({ page }) => {
    await logInUser(page, email, password)
    await page.goto("/settings")
    await page.getByRole("tab", { name: "My profile" }).click()
  })

  test("Edit user name with a valid name", async ({ page }) => {
    const updatedName = "Test User 2"

    await page.getByRole("button", { name: "Edit" }).click()
    await typeInto(page.getByLabel("Full name"), updatedName)
    await page.getByRole("button", { name: "Save" }).click()

    await expect(page.getByText("User updated successfully")).toBeVisible()
    await expect(
      page.locator("form").getByText(updatedName, { exact: true }),
    ).toBeVisible()
  })

  test("Edit user email with an invalid email shows error", async ({
    page,
  }) => {
    await page.getByRole("button", { name: "Edit" }).click()
    await page.getByLabel("Email").fill("")
    await page.locator("body").click()

    await expect(page.getByText("Invalid email address")).toBeVisible()
  })
})

test.describe("Edit user email", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("A new email takes effect only once its link is confirmed", async ({
    page,
    request,
  }) => {
    const email = randomEmail()
    const password = randomPassword()
    const updatedEmail = randomEmail()

    await createUser({ email, password })
    await logInUser(page, email, password)
    await page.goto("/settings")
    await page.getByRole("tab", { name: "My profile" }).click()

    await page.getByRole("button", { name: "Edit" }).click()
    await typeInto(page.getByLabel("Email"), updatedEmail)
    await page.getByTestId("current-password-input").fill(password)
    await page.getByRole("button", { name: "Save" }).click()

    await expect(
      page.getByText("Check your new email to confirm the change"),
    ).toBeVisible()
    await expect(
      page.locator("form").getByText(email, { exact: true }),
    ).toBeVisible()

    const html = await waitForEmailHtml({
      request,
      query: `to:${updatedEmail}`,
    })
    await page.goto(`/confirm-email?token=${emailedToken(html)}`)
    await page.getByRole("button", { name: "Confirm email" }).click()

    await expect(page).toHaveURL(/\/login$/)
    await logInUser(page, updatedEmail, password)
    await page.goto("/settings")
    await page.getByRole("tab", { name: "My profile" }).click()
    await expect(
      page.locator("form").getByText(updatedEmail, { exact: true }),
    ).toBeVisible()
  })

  test("An email change link works once", async ({ page, request }) => {
    const email = randomEmail()
    const password = randomPassword()
    const updatedEmail = randomEmail()

    await createUser({ email, password })
    await logInUser(page, email, password)
    await page.goto("/settings")
    await page.getByRole("tab", { name: "My profile" }).click()
    await page.getByRole("button", { name: "Edit" }).click()
    await typeInto(page.getByLabel("Email"), updatedEmail)
    await page.getByTestId("current-password-input").fill(password)
    await page.getByRole("button", { name: "Save" }).click()

    const html = await waitForEmailHtml({
      request,
      query: `to:${updatedEmail}`,
    })
    const link = `/confirm-email?token=${emailedToken(html)}`
    await page.goto(link)
    await page.getByRole("button", { name: "Confirm email" }).click()
    await expect(page).toHaveURL(/\/login$/)

    await page.goto(link)
    await page.getByRole("button", { name: "Confirm email" }).click()

    await expect(page.getByText("Invalid token")).toBeVisible()
  })

  test("Changing the email asks for the current password", async ({ page }) => {
    const email = randomEmail()
    const password = randomPassword()

    await createUser({ email, password })
    await logInUser(page, email, password)
    await page.goto("/settings")
    await page.getByRole("tab", { name: "My profile" }).click()
    await page.getByRole("button", { name: "Edit" }).click()
    await typeInto(page.getByLabel("Email"), randomEmail())
    await page.getByRole("button", { name: "Save" }).click()

    await expect(
      page.getByText("Current password is required to change the email"),
    ).toBeVisible()
  })

  test("A wrong current password changes nothing", async ({ page }) => {
    const email = randomEmail()
    const password = randomPassword()

    await createUser({ email, password })
    await logInUser(page, email, password)
    await page.goto("/settings")
    await page.getByRole("tab", { name: "My profile" }).click()
    await page.getByRole("button", { name: "Edit" }).click()
    await typeInto(page.getByLabel("Email"), randomEmail())
    await page.getByTestId("current-password-input").fill(randomPassword())
    await page.getByRole("button", { name: "Save" }).click()

    await expect(page.getByText("Incorrect password")).toBeVisible()
    await expect(
      page.getByText("Check your new email to confirm the change"),
    ).not.toBeVisible()
  })

  test("An address already in use gets the same confirmation", async ({
    page,
  }) => {
    const email = randomEmail()
    const taken = randomEmail()
    const password = randomPassword()

    await createUser({ email: taken, password })
    await createUser({ email, password })
    await logInUser(page, email, password)
    await page.goto("/settings")
    await page.getByRole("tab", { name: "My profile" }).click()
    await page.getByRole("button", { name: "Edit" }).click()
    await typeInto(page.getByLabel("Email"), taken)
    await page.getByTestId("current-password-input").fill(password)
    await page.getByRole("button", { name: "Save" }).click()

    await expect(
      page.getByText("Check your new email to confirm the change"),
    ).toBeVisible()
  })
})

test.describe("Full name is required", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("Clearing the full name shows an error and does not save", async ({
    page,
  }) => {
    const email = randomEmail()
    const password = randomPassword()
    await createUser({ email, password })
    await logInUser(page, email, password)
    await page.goto("/settings")

    await page.getByRole("button", { name: "Edit" }).click()
    await page.getByLabel("Full name").click()
    await page.getByLabel("Full name").press("ControlOrMeta+a")
    await page.getByLabel("Full name").press("Backspace")
    await page.getByRole("button", { name: "Save" }).click()

    await expect(page.getByText("Full name is required")).toBeVisible()
    await expect(page.getByText("User updated successfully")).not.toBeVisible()
  })
})

test.describe("Cancel edit actions", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("Cancel edit action restores original name", async ({ page }) => {
    const email = randomEmail()
    const password = randomPassword()
    const user = await createUser({ email, password })

    await logInUser(page, email, password)
    await page.goto("/settings")
    await page.getByRole("tab", { name: "My profile" }).click()
    await page.getByRole("button", { name: "Edit" }).click()
    await page.getByLabel("Full name").fill("Test User")
    await page.getByRole("button", { name: "Cancel" }).first().click()

    await expect(
      page.locator("form").getByText(user.full_name as string, { exact: true }),
    ).toBeVisible()
  })

  test("Cancel edit action restores original email", async ({ page }) => {
    const email = randomEmail()
    const password = randomPassword()
    await createUser({ email, password })

    await logInUser(page, email, password)
    await page.goto("/settings")
    await page.getByRole("tab", { name: "My profile" }).click()
    await page.getByRole("button", { name: "Edit" }).click()
    await page.getByLabel("Email").fill(randomEmail())
    await page.getByRole("button", { name: "Cancel" }).first().click()

    await expect(
      page.locator("form").getByText(email, { exact: true }),
    ).toBeVisible()
  })
})

test.describe("Change password", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("Update password successfully", async ({ page }) => {
    const email = randomEmail()
    const password = randomPassword()
    const newPassword = randomPassword()

    await createUser({ email, password })
    await logInUser(page, email, password)

    await page.goto("/settings")
    await page.getByRole("tab", { name: "Password" }).click()
    await page.getByTestId("current-password-input").fill(password)
    await page.getByTestId("new-password-input").fill(newPassword)
    await page.getByTestId("confirm-password-input").fill(newPassword)
    await page.getByRole("button", { name: "Update Password" }).click()

    await expect(page.getByText("Password updated successfully")).toBeVisible()

    await logOutUser(page)
    await logInUser(page, email, newPassword)
  })
})

test.describe("Sessions after a security change", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("Changing the password signs the other devices out", async ({
    page,
    browser,
  }) => {
    const email = randomEmail()
    const password = randomPassword()
    const newPassword = randomPassword()
    await createUser({ email, password })
    const other = await browser.newContext()
    const otherPage = await other.newPage()
    await logInUser(otherPage, email, password)
    await logInUser(page, email, password)

    await page.goto("/settings")
    await page.getByRole("tab", { name: "Password" }).click()
    await page.getByTestId("current-password-input").fill(password)
    await page.getByTestId("new-password-input").fill(newPassword)
    await page.getByTestId("confirm-password-input").fill(newPassword)
    await page.getByRole("button", { name: "Update Password" }).click()
    await expect(page.getByText("Password updated successfully")).toBeVisible()

    await page.goto("/settings")
    await expect(page.getByRole("tab", { name: "My profile" })).toBeVisible()
    await otherPage.goto("/settings")
    await expect(otherPage).toHaveURL(/\/login$/)
    await other.close()
  })

  test("Logging out signs the user out everywhere", async ({
    page,
    browser,
  }) => {
    const email = randomEmail()
    const password = randomPassword()
    await createUser({ email, password })
    const other = await browser.newContext()
    const otherPage = await other.newPage()
    await logInUser(otherPage, email, password)
    await logInUser(page, email, password)

    await logOutUser(page)

    await otherPage.goto("/settings")
    await expect(otherPage).toHaveURL(/\/login$/)
    await other.close()
  })
})

test.describe("Change password validation", () => {
  test.use({ storageState: { cookies: [], origins: [] } })
  let email: string
  let password: string

  test.beforeAll(async () => {
    email = randomEmail()
    password = randomPassword()
    await createUser({ email, password })
  })

  test.beforeEach(async ({ page }) => {
    await logInUser(page, email, password)
    await page.goto("/settings")
    await page.getByRole("tab", { name: "Password" }).click()
  })

  test("Update password with weak passwords", async ({ page }) => {
    const weakPassword = "weak"

    await page.getByTestId("current-password-input").fill(password)
    await page.getByTestId("new-password-input").fill(weakPassword)
    await page.getByTestId("confirm-password-input").fill(weakPassword)
    await page.getByRole("button", { name: "Update Password" }).click()

    await expect(
      page.getByText("Password must be at least 8 characters"),
    ).toBeVisible()
  })

  test("An empty current password is rejected", async ({ page }) => {
    const newPassword = randomPassword()

    await page.getByTestId("new-password-input").fill(newPassword)
    await page.getByTestId("confirm-password-input").fill(newPassword)
    await page.getByRole("button", { name: "Update Password" }).click()

    await expect(page.getByText("Current password is required")).toBeVisible()
  })

  test("New password and confirmation password do not match", async ({
    page,
  }) => {
    await page.getByTestId("current-password-input").fill(password)
    await page.getByTestId("new-password-input").fill(randomPassword())
    await page.getByTestId("confirm-password-input").fill(randomPassword())
    await page.getByRole("button", { name: "Update Password" }).click()

    await expect(page.getByText("The passwords don't match")).toBeVisible()
  })

  test("Current password and new password are the same", async ({ page }) => {
    await page.getByTestId("current-password-input").fill(password)
    await page.getByTestId("new-password-input").fill(password)
    await page.getByTestId("confirm-password-input").fill(password)
    await page.getByRole("button", { name: "Update Password" }).click()

    await expect(
      page.getByText("New password cannot be the same as the current one"),
    ).toBeVisible()
  })
})

test.describe("Delete account", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("Delete own account and sign in is no longer possible", async ({
    page,
  }) => {
    const email = randomEmail()
    const password = randomPassword()

    await createUser({ email, password })
    await logInUser(page, email, password)

    await page.goto("/settings")
    await page.getByRole("tab", { name: "Danger zone" }).click()
    await page.getByRole("button", { name: "Delete Account" }).click()
    await page.getByTestId("delete-account-password-input").fill(password)
    await page.getByRole("button", { name: "Delete", exact: true }).click()

    await page.waitForURL("/login")

    await page.getByTestId("email-input").fill(email)
    await page.getByTestId("password-input").fill(password)
    await page.getByRole("button", { name: "Log In" }).click()
    await expect(page.getByText("Incorrect email or password")).toBeVisible()
  })
})

test.describe("Delete account confirmation", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("Deleting needs a password and a wrong one keeps the account", async ({
    page,
  }) => {
    const email = randomEmail()
    const password = randomPassword()

    await createUser({ email, password })
    await logInUser(page, email, password)
    await page.goto("/settings")
    await page.getByRole("tab", { name: "Danger zone" }).click()
    await page.getByRole("button", { name: "Delete Account" }).click()

    await expect(
      page.getByRole("button", { name: "Delete", exact: true }),
    ).toBeDisabled()
    await page
      .getByTestId("delete-account-password-input")
      .fill(randomPassword())
    await page.getByRole("button", { name: "Delete", exact: true }).click()

    await expect(page.getByText("Incorrect password")).toBeVisible()
    await page.goto("/settings")
    await expect(page.getByRole("tab", { name: "My profile" })).toBeVisible()
  })
})

test("Superuser cannot delete their own account", async ({ page }) => {
  await page.goto("/settings")
  await page.getByRole("tab", { name: "Danger zone" }).click()
  await page.getByRole("button", { name: "Delete Account" }).click()
  await page
    .getByTestId("delete-account-password-input")
    .fill(firstSuperuserPassword)
  await page.getByRole("button", { name: "Delete", exact: true }).click()

  await expect(
    page.getByText("Super users are not allowed to delete themselves"),
  ).toBeVisible()
})

test("Appearance is in the user menu", async ({ page }) => {
  await page.goto("/settings")
  await page.getByTestId("user-menu").click()
  await expect(page.getByTestId("theme-button")).toBeVisible()
})

test("User can switch between theme modes", async ({ page }) => {
  await page.goto("/settings")

  await openAppearanceMenu(page)
  await page.getByTestId("dark-mode").click()
  await expect(page.locator("html")).toHaveClass(/dark/)

  await expect(page.getByTestId("dark-mode")).not.toBeVisible()

  await openAppearanceMenu(page)
  await page.getByTestId("light-mode").click()
  await expect(page.locator("html")).toHaveClass(/light/)
})

test.describe("Selected mode across sessions", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("Selected mode is preserved across sessions", async ({ page }) => {
    const email = randomEmail()
    const password = randomPassword()

    await createUser({ email, password })
    await logInUser(page, email, password)
    await page.goto("/settings")

    await openAppearanceMenu(page)
    await page.getByTestId("light-mode").click()
    await expect(page.locator("html")).toHaveClass(/light/)

    await openAppearanceMenu(page)
    await page.getByTestId("dark-mode").click()
    await expect(page.locator("html")).toHaveClass(/dark/)

    await logOutUser(page)
    await logInUser(page, email, password)

    await expect(page.locator("html")).toHaveClass(/dark/)
  })
})
