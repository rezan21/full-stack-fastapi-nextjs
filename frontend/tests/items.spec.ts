import { expect, type Page, test } from "@playwright/test"
import { createUser } from "./utils/privateApi"
import {
  randomEmail,
  randomItemDescription,
  randomItemTitle,
  randomPassword,
} from "./utils/random"
import { typeInto } from "./utils/type"
import { logInUser } from "./utils/user"

const API_BASE = `${process.env.API_URL ?? "http://localhost:8000"}/api/v1`

const sheet = (page: Page) => page.locator('[data-slot="sheet-content"]')

test("Items page is accessible and shows correct title", async ({ page }) => {
  await page.goto("/items")
  await expect(page.getByRole("heading", { name: "Items" })).toBeVisible()
  await expect(page.getByText("Create and manage your items")).toBeVisible()
})

test("Add Item button is visible", async ({ page }) => {
  await page.goto("/items")
  await expect(page.getByRole("button", { name: "Add Item" })).toBeVisible()
})

test.describe("Items management", () => {
  test.use({ storageState: { cookies: [], origins: [] } })
  let email: string
  const password = randomPassword()

  test.beforeAll(async () => {
    email = randomEmail()
    await createUser({ email, password })
  })

  test.beforeEach(async ({ page }) => {
    await logInUser(page, email, password)
    await page.goto("/items")
  })

  test("Create a new item successfully", async ({ page }) => {
    const title = randomItemTitle()
    const description = randomItemDescription()

    await page.getByRole("button", { name: "Add Item" }).click()
    await page.getByLabel("Title").fill(title)
    await page.getByLabel("Description").fill(description)
    await page.getByRole("button", { name: "Save" }).click()

    await expect(page.getByText("Item created successfully")).toBeVisible()
    await expect(page.getByText(title)).toBeVisible()
  })

  test("Create item with only required fields", async ({ page }) => {
    const title = randomItemTitle()

    await page.getByRole("button", { name: "Add Item" }).click()
    await page.getByLabel("Title").fill(title)
    await page.getByRole("button", { name: "Save" }).click()

    await expect(page.getByText("Item created successfully")).toBeVisible()
    await expect(page.getByText(title)).toBeVisible()
  })

  test("Cancel item creation", async ({ page }) => {
    await page.getByRole("button", { name: "Add Item" }).click()
    await page.getByLabel("Title").fill("Test Item")
    await page.getByRole("button", { name: "Cancel" }).click()

    await expect(page.getByRole("dialog")).not.toBeVisible()
  })

  test("Title is required", async ({ page }) => {
    await page.getByRole("button", { name: "Add Item" }).click()
    await page.getByLabel("Title").fill("")
    await page.getByLabel("Title").blur()

    await expect(page.getByText("Title is required")).toBeVisible()
  })

  test.describe("Edit and Delete", () => {
    let itemTitle: string

    test.beforeEach(async ({ page }) => {
      itemTitle = randomItemTitle()

      await page.getByRole("button", { name: "Add Item" }).click()
      await page.getByLabel("Title").fill(itemTitle)
      await page.getByRole("button", { name: "Save" }).click()
      await expect(page.getByText("Item created successfully")).toBeVisible()
      await expect(page.getByRole("dialog")).not.toBeVisible()
    })

    test("Edit an item successfully", async ({ page }) => {
      const itemRow = page.getByRole("row").filter({ hasText: itemTitle })
      await itemRow.getByRole("button").last().click()
      await page.getByRole("menuitem", { name: "Edit Item" }).click()

      const updatedTitle = randomItemTitle()
      const updatedDescription = randomItemDescription()
      await typeInto(page.getByLabel("Title"), updatedTitle)
      await typeInto(page.getByLabel("Description"), updatedDescription)
      await page.getByRole("button", { name: "Save" }).click()

      await expect(page.getByText("Item updated successfully")).toBeVisible()
      await expect(page.getByText(updatedTitle)).toBeVisible()
      await expect(page.getByText(updatedDescription)).toBeVisible()
    })

    test("The edit dialog reopens with saved values and drops cancelled typing", async ({
      page,
    }) => {
      const openEdit = async (title: string) => {
        const row = page.getByRole("row").filter({ hasText: title })
        await row.getByRole("button").last().click()
        await page.getByRole("menuitem", { name: "Edit Item" }).click()
      }

      await openEdit(itemTitle)
      const updatedTitle = randomItemTitle()
      await typeInto(page.getByLabel("Title"), updatedTitle)
      await page.getByRole("button", { name: "Save" }).click()
      await expect(page.getByText("Item updated successfully")).toBeVisible()
      await expect(page.getByRole("dialog")).not.toBeVisible()

      await openEdit(updatedTitle)
      await expect(page.getByLabel("Title")).toHaveValue(updatedTitle)
      await typeInto(page.getByLabel("Title"), "discarded")
      await page.getByRole("button", { name: "Cancel" }).click()
      await expect(page.getByRole("dialog")).not.toBeVisible()

      await openEdit(updatedTitle)
      await expect(page.getByLabel("Title")).toHaveValue(updatedTitle)
    })

    test("Opening an item shows it in a sheet over the list", async ({
      page,
    }) => {
      await page.getByRole("link", { name: itemTitle }).click()

      await expect(page).toHaveURL(/\/items\/[\w-]+$/)
      await expect(
        sheet(page).getByRole("heading", { name: itemTitle }),
      ).toBeVisible()
      await expect(sheet(page).getByText("No description")).toBeVisible()
      await expect(page.getByText("Create and manage your items")).toBeVisible()
    })

    test("Closing the sheet returns to the list", async ({ page }) => {
      await page.getByRole("link", { name: itemTitle }).click()
      await sheet(page).getByRole("button", { name: "Close" }).click()

      await expect(sheet(page)).not.toBeVisible()
      await expect(page).toHaveURL(/\/items$/)
    })

    test("Browser back closes the sheet", async ({ page }) => {
      await page.getByRole("link", { name: itemTitle }).click()
      await expect(sheet(page)).toBeVisible()
      await page.goBack()

      await expect(sheet(page)).not.toBeVisible()
      await expect(page).toHaveURL(/\/items$/)
    })

    test("The item URL opens the full page, not the sheet", async ({
      page,
    }) => {
      const href = await page
        .getByRole("link", { name: itemTitle })
        .getAttribute("href")
      await page.goto(href as string)

      await expect(page.getByRole("heading", { name: itemTitle })).toBeVisible()
      await expect(
        page.getByRole("button", { name: "Back to items" }),
      ).toBeVisible()
      await expect(sheet(page)).not.toBeVisible()
    })

    test("Refreshing with the sheet open shows the full page", async ({
      page,
    }) => {
      await page.getByRole("link", { name: itemTitle }).click()
      await expect(sheet(page)).toBeVisible()
      await page.reload()

      await expect(
        page.getByRole("button", { name: "Back to items" }),
      ).toBeVisible()
      await expect(sheet(page)).not.toBeVisible()
    })

    test("Edit an item from its sheet", async ({ page }) => {
      await page.getByRole("link", { name: itemTitle }).click()
      await sheet(page).getByRole("button", { name: "Item actions" }).click()
      await page.getByRole("menuitem", { name: "Edit Item" }).click()

      const updatedTitle = randomItemTitle()
      await typeInto(page.getByLabel("Title"), updatedTitle)
      await page.getByRole("button", { name: "Save" }).click()

      await expect(page.getByText("Item updated successfully")).toBeVisible()
      await expect(
        sheet(page).getByRole("heading", { name: updatedTitle }),
      ).toBeVisible()
    })

    test("Delete an item from its sheet", async ({ page }) => {
      await page.getByRole("link", { name: itemTitle }).click()
      await sheet(page).getByRole("button", { name: "Item actions" }).click()
      await page.getByRole("menuitem", { name: "Delete Item" }).click()
      const confirm = page
        .getByRole("alertdialog")
        .getByRole("button", { name: "Delete" })
      await confirm.focus()
      await page.keyboard.press("Enter")

      await expect(
        page.getByText("The item was deleted successfully"),
      ).toBeVisible()
      await expect(sheet(page)).not.toBeVisible()
      await expect(page).toHaveURL(/\/items$/)
      await expect(page.getByText(itemTitle)).not.toBeVisible()
    })

    test("Opening an item deleted elsewhere shows not found in the sheet", async ({
      page,
    }) => {
      const href = (await page
        .getByRole("link", { name: itemTitle })
        .getAttribute("href")) as string
      const token = (await page.context().cookies()).find(
        (cookie) => cookie.name === "access_token",
      )?.value
      await fetch(`${API_BASE}/items/${href.split("/").pop()}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      })

      await page.getByRole("link", { name: itemTitle }).click()

      await expect(
        sheet(page).getByRole("heading", { name: "Item not found" }),
      ).toBeVisible()
    })

    test("Delete an item successfully", async ({ page }) => {
      const itemRow = page.getByRole("row").filter({ hasText: itemTitle })
      await itemRow.getByRole("button").last().click()
      await page.getByRole("menuitem", { name: "Delete Item" }).click()

      await page.getByRole("button", { name: "Delete" }).click()

      await expect(
        page.getByText("The item was deleted successfully"),
      ).toBeVisible()
      await expect(page.getByText(itemTitle)).not.toBeVisible()
    })
  })
})

test.describe("Item detail page not found", () => {
  for (const id of ["00000000-0000-0000-0000-000000000000", "not-a-uuid"]) {
    test(`Shows not found for ${id}`, async ({ page }) => {
      await page.goto(`/items/${id}`)

      await expect(
        page.getByRole("heading", { name: "Page not found" }),
      ).toBeVisible()
    })
  }
})

test.describe("Items empty state", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("Shows empty state message when no items exist", async ({ page }) => {
    const email = randomEmail()
    const password = randomPassword()
    await createUser({ email, password })
    await logInUser(page, email, password)

    await page.goto("/items")

    await expect(page.getByText("You don't have any items yet")).toBeVisible()
    await expect(page.getByText("Add a new item to get started")).toBeVisible()
  })
})
