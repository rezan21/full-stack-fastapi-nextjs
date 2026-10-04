import type { Locator } from "@playwright/test"

// Types text into a field, replacing its content.
export async function typeInto(field: Locator, text: string) {
  await field.click()
  await field.press("ControlOrMeta+a")
  await field.pressSequentially(text)
}
