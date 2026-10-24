"use client"

import { MessagePrimitive, useAuiState } from "@assistant-ui/react"
import { Bubble, BubbleContent } from "@/components/ui/bubble"
import { Message, MessageContent } from "@/components/ui/message"
import { MessageScrollerItem } from "@/components/ui/message-scroller"
import { Markdown } from "./Markdown"

// One message of the conversation, read from the message the thread provides.
export function ChatMessageRow() {
  const id = useAuiState((s) => s.message.id)
  const isUser = useAuiState((s) => s.message.role === "user")
  const isBlank = useAuiState(
    (s) =>
      !s.message.parts.some(
        (part) =>
          part.type === "tool-call" ||
          (part.type === "text" && part.text !== ""),
      ),
  )
  if (isBlank) return null

  return (
    <MessageScrollerItem messageId={id} scrollAnchor={isUser}>
      <Message align={isUser ? "end" : "start"}>
        <MessageContent>
          <MessagePrimitive.Parts>
            {({ part }) => {
              if (part.type === "tool-call") return part.toolUI ?? null
              if (part.type === "text" && part.text) {
                return <TextPart text={part.text} isUser={isUser} />
              }
              return null
            }}
          </MessagePrimitive.Parts>
        </MessageContent>
      </Message>
    </MessageScrollerItem>
  )
}

// The text of a message, in a bubble that suits who said it.
function TextPart({ text, isUser }: { text: string; isUser: boolean }) {
  if (isUser) {
    return (
      <Bubble align="end">
        <BubbleContent className="whitespace-pre-wrap">{text}</BubbleContent>
      </Bubble>
    )
  }
  return (
    <Bubble variant="ghost">
      <BubbleContent>
        <Markdown>{text}</Markdown>
      </BubbleContent>
    </Bubble>
  )
}
