import { describe, expect, test } from "bun:test"
import type { Message } from "@ag-ui/client"
import {
  chatErrorMessage,
  earlierMessagesNote,
  GENERIC_CHAT_ERROR,
  isRejection,
  isUnauthorized,
  toChatMessages,
} from "@/lib/chat"

const user = (id: string, content: Message["content"]) =>
  ({ id, role: "user", content }) as Message
const assistant = (id: string, content?: string) =>
  ({ id, role: "assistant", content }) as Message

function httpError(status: number, payload: unknown) {
  return Object.assign(new Error(`HTTP ${status}`), { status, payload })
}

describe("toChatMessages", () => {
  test("keeps what the user and the assistant said, in order", () => {
    expect(
      toChatMessages([user("1", "Hello"), assistant("2", "Hi there")]),
    ).toEqual([
      { id: "1", role: "user", content: "Hello" },
      { id: "2", role: "assistant", content: "Hi there" },
    ])
  })

  test("leaves out tool calls, tool results and system messages", () => {
    const messages = [
      user("1", "Look around"),
      {
        id: "2",
        role: "assistant",
        toolCalls: [{ id: "c", type: "function", function: {} }],
      },
      { id: "3", role: "tool", toolCallId: "c", content: "files" },
      { id: "4", role: "system", content: "be nice" },
      assistant("5", "Done"),
    ] as Message[]
    expect(toChatMessages(messages).map((m) => m.id)).toEqual(["1", "5"])
  })

  test("leaves out messages with no text yet", () => {
    expect(toChatMessages([user("1", "Hi"), assistant("2", "")])).toHaveLength(
      1,
    )
    expect(toChatMessages([assistant("2", undefined)])).toHaveLength(0)
  })

  test("reads the text of a message made of parts", () => {
    const parts = [
      { type: "text", text: "One " },
      { type: "text", text: "two" },
    ] as Message["content"]
    expect(toChatMessages([user("1", parts)])[0].content).toBe("One two")
  })
})

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
