"use client"

import { ThreadPrimitive, useAuiState } from "@assistant-ui/react"
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
import { useChat } from "@/hooks/use-chat"
import { earlierMessagesNote } from "@/lib/chat"
import { ChatInput } from "./ChatInput"
import { ChatMessageRow } from "./ChatMessageRow"

// The messages and the box for writing to the assistant.
export function ChatPanel({
  error,
  clearError,
  shown,
  total,
}: {
  error?: string
  clearError: () => void
  shown: number
  total: number
}) {
  const { send, stop } = useChat(clearError)
  const isEmpty = useAuiState((s) => s.thread.isEmpty)
  const isRunning = useAuiState((s) => s.thread.isRunning)
  const isThinking = useAuiState(
    (s) => s.thread.isRunning && s.thread.messages.at(-1)?.role !== "assistant",
  )
  const note = earlierMessagesNote(shown, total)

  return (
    <div className="flex h-[calc(100svh-16rem)] min-h-96 flex-col gap-4">
      {isEmpty && !isThinking ? (
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
                <ThreadPrimitive.Messages>
                  {() => <ChatMessageRow />}
                </ThreadPrimitive.Messages>
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
