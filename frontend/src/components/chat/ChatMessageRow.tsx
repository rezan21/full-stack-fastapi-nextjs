import { Bubble, BubbleContent } from "@/components/ui/bubble"
import { Message, MessageContent } from "@/components/ui/message"
import type { ChatMessage } from "@/lib/chat"
import { Markdown } from "./Markdown"

// One message of a conversation.
export function ChatMessageRow({ message }: { message: ChatMessage }) {
  if (message.role === "user") {
    return (
      <Message align="end">
        <MessageContent>
          <Bubble align="end">
            <BubbleContent className="whitespace-pre-wrap">
              {message.content}
            </BubbleContent>
          </Bubble>
        </MessageContent>
      </Message>
    )
  }
  return (
    <Message>
      <MessageContent>
        <Bubble variant="ghost">
          <BubbleContent>
            <Markdown>{message.content}</Markdown>
          </BubbleContent>
        </Bubble>
      </MessageContent>
    </Message>
  )
}
