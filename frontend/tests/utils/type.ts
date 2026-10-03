import type { Locator } from "@playwright/test"

export async function typeInto(field: Locator, text: string) {
  await field.click()
  await field.press("ControlOrMeta+a")
  await field.pressSequentially(text)
}
