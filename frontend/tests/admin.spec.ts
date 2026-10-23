import { expect, test } from "@playwright/test"
import { e2ePassword, e2eUserEmail } from "./config"
import { createItemAs, deleteItemAs, loginAs } from "./utils/api"
import { randomItemTitle } from "./utils/random"

test("Superuser cannot delete their own account", async ({ page }) => {
  await page.goto("/settings")
  await page.getByRole("tab", { name: "Danger zone" }).click()
  await page.getByRole("button", { name: "Delete Account" }).click()
  await page.getByTestId("delete-account-password-input").fill(e2ePassword)
  await page.getByRole("button", { name: "Delete", exact: true }).click()

  await expect(
    page.getByText("Super users are not allowed to delete themselves"),
  ).toBeVisible()
})

test("The items list includes items of other users", async ({ page }) => {
  const token = await loginAs(e2eUserEmail, e2ePassword)
  const title = randomItemTitle()
  const id = await createItemAs(token, title)
  try {
    await page.goto("/items")
    await expect(page.getByText(title)).toBeVisible()
  } finally {
    await deleteItemAs(token, id)
  }
})

test("An admin can open another user's item", async ({ page }) => {
  const token = await loginAs(e2eUserEmail, e2ePassword)
  const title = randomItemTitle()
  const id = await createItemAs(token, title)
  try {
    await page.goto(`/items/${id}`)
    await expect(page.getByRole("heading", { name: title })).toBeVisible()
  } finally {
    await deleteItemAs(token, id)
  }
})
