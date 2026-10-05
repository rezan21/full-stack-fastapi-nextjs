import { describe, expect, test } from "bun:test"
import { formatActivity, formatCreated, getInitials } from "@/lib/utils"

describe("getInitials", () => {
  test("takes the first letters of the first two words", () => {
    expect(getInitials("ada king lovelace")).toBe("AK")
    expect(getInitials("Ada")).toBe("A")
  })
})

describe("formatCreated", () => {
  test("formats the date in UTC", () => {
    expect(formatCreated("2026-10-03T23:59:59Z")).toBe(
      "Created October 3, 2026",
    )
  })

  test("returns nothing without a date", () => {
    expect(formatCreated(null)).toBeUndefined()
    expect(formatCreated(undefined)).toBeUndefined()
    expect(formatCreated("")).toBeUndefined()
  })
})

describe("formatActivity", () => {
  test("formats the date of the last activity in UTC", () => {
    expect(formatActivity("2026-10-03T23:59:59Z")).toBe("Oct 3, 2026")
  })
})
