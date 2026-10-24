"use client"

import { Sparkles } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty"
import { Message, MessageContent } from "@/components/ui/message"
import {
  MessageScroller,
  MessageScrollerButton,
  MessageScrollerContent,
  MessageScrollerItem,
  MessageScrollerProvider,
  MessageScrollerViewport,
} from "@/components/ui/message-scroller"
import { earlierMessagesNote } from "@/lib/chat"
import { ChatInput } from "./ChatInput"
import { ChatMessageRow, type ChatRow } from "./ChatMessageRow"

export type ChatState = {
  messages: ChatRow[]
  isRunning: boolean
  error?: string
  send: (text: string) => Promise<boolean>
  stop: () => void
}

// The messages and the box for writing to the assistant.
export function ChatPanel({
  chat,
  shown,
  total,
}: {
  chat: ChatState
  shown: number
  total: number
}) {
  const { messages, isRunning, error, send, stop } = chat
  const isThinking = isRunning && messages.at(-1)?.role !== "assistant"
  const note = earlierMessagesNote(shown, total)

  return (
    <div className="flex h-[calc(100svh-19rem)] min-h-96 flex-col gap-4">
      {messages.length === 0 && !isThinking ? (
        <Empty className="flex-1">
          <EmptyHeader>
            <EmptyMedia variant="icon">
              <Sparkles />
            </EmptyMedia>
            <EmptyTitle>Start the conversation</EmptyTitle>
            <EmptyDescription>Ask the assistant anything</EmptyDescription>
          </EmptyHeader>
        </Empty>
      ) : (
        <MessageScrollerProvider autoScroll>
          <MessageScroller>
            <MessageScrollerViewport>
              <MessageScrollerContent>
                {messages.map((message) => (
                  <MessageScrollerItem
                    key={message.id}
                    messageId={message.id}
                    scrollAnchor={message.role === "user"}
                  >
                    <ChatMessageRow message={message} />
                  </MessageScrollerItem>
                ))}
                {isThinking && (
                  <MessageScrollerItem messageId="thinking">
                    <Message>
                      <MessageContent>
                        <span className="shimmer text-muted-foreground">
                          Thinking
                        </span>
                      </MessageContent>
                    </Message>
                  </MessageScrollerItem>
                )}
              </MessageScrollerContent>
            </MessageScrollerViewport>
            <MessageScrollerButton />
          </MessageScroller>
        </MessageScrollerProvider>
      )}
      {note && (
        <p className="text-center text-xs text-muted-foreground">{note}</p>
      )}
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      <ChatInput isRunning={isRunning} onSend={send} onStop={stop} />
    </div>
  )
}
