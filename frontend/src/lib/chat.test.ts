import { describe, expect, test } from "bun:test"
import {
  chatErrorMessage,
  earlierMessagesNote,
  GENERIC_CHAT_ERROR,
  isRejection,
  isUnauthorized,
} from "@/lib/chat"

function httpError(status: number, payload: unknown) {
  return Object.assign(new Error(`HTTP ${status}`), { status, payload })
}

describe("chatErrorMessage", () => {
  test("shows the reason the API gave", () => {
    const error = httpError(429, { detail: "Too many messages. Try later." })
    expect(chatErrorMessage(error)).toBe("Too many messages. Try later.")
  })

  test("falls back to a generic message for anything else", () => {
    expect(chatErrorMessage(httpError(500, "boom"))).toBe(GENERIC_CHAT_ERROR)
    expect(chatErrorMessage(httpError(422, { detail: [{ msg: "x" }] }))).toBe(
      GENERIC_CHAT_ERROR,
    )
    expect(chatErrorMessage(new TypeError("network down"))).toBe(
      GENERIC_CHAT_ERROR,
    )
    expect(chatErrorMessage("nonsense")).toBe(GENERIC_CHAT_ERROR)
    expect(chatErrorMessage(undefined)).toBe(GENERIC_CHAT_ERROR)
  })
})

describe("isUnauthorized", () => {
  test("is true only for a 401", () => {
    expect(isUnauthorized(httpError(401, {}))).toBe(true)
    expect(isUnauthorized(httpError(403, {}))).toBe(false)
    expect(isUnauthorized(new Error("plain"))).toBe(false)
    expect(isUnauthorized(null)).toBe(false)
  })
})

describe("isRejection", () => {
  test("is true when the API answered with an error status", () => {
    expect(isRejection(httpError(429, {}))).toBe(true)
    expect(isRejection(httpError(400, "bad"))).toBe(true)
  })

  test("is false for a failure with no answer, such as a dropped connection", () => {
    expect(isRejection(new TypeError("network down"))).toBe(false)
    expect(isRejection(new Error("plain"))).toBe(false)
    expect(isRejection(null)).toBe(false)
  })
})

describe("earlierMessagesNote", () => {
  test("says how much of a long conversation is shown", () => {
    expect(earlierMessagesNote(100, 1234)).toBe(
      "Showing the latest 100 of 1,234 messages.",
    )
  })

  test("says nothing when every message is shown", () => {
    expect(earlierMessagesNote(100, 100)).toBeUndefined()
    expect(earlierMessagesNote(0, 0)).toBeUndefined()
  })
})
