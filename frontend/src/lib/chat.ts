import { contentToText, type Message } from "@ag-ui/client"
import type { ChatMessagePublic } from "@/client"

export type ChatMessage = Pick<ChatMessagePublic, "id" | "role" | "content">

export const GENERIC_CHAT_ERROR = "Something went wrong. Please try again."

type HttpFailure = Error & { status?: number; payload?: unknown }

// Returns what the user and the assistant said, leaving out tool calls and system messages.
export function toChatMessages(messages: readonly Message[]): ChatMessage[] {
  return messages.flatMap((message) => {
    if (message.role !== "user" && message.role !== "assistant") return []
    const content = message.content ? contentToText(message.content) : ""
    return content.trim()
      ? [{ id: message.id, role: message.role, content }]
      : []
  })
}

// Returns the reason the API gave for a failed run, or a generic message.
export function chatErrorMessage(error: unknown): string {
  const payload = (error as HttpFailure | undefined)?.payload
  if (payload && typeof payload === "object" && "detail" in payload) {
    if (typeof payload.detail === "string") return payload.detail
  }
  return GENERIC_CHAT_ERROR
}

// Returns whether a failed run was rejected for lack of a valid session.
export function isUnauthorized(error: unknown): boolean {
  return (error as HttpFailure | null)?.status === 401
}

// Returns whether the API turned a run down, as opposed to the connection failing.
export function isRejection(error: unknown): boolean {
  return typeof (error as HttpFailure | null)?.status === "number"
}

// Returns a note saying how much of a long conversation is shown, if not all of it.
export function earlierMessagesNote(
  shown: number,
  total: number,
): string | undefined {
  if (total <= shown) return undefined
  return `Showing the latest ${shown.toLocaleString("en-US")} of ${total.toLocaleString("en-US")} messages.`
}
