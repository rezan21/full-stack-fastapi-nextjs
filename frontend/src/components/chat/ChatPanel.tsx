"use client"

import { ThreadPrimitive, useAuiState } from "@assistant-ui/react"
import { ArrowDown, Sparkles } from "lucide-react"
import { Suggestions } from "@/components/assistant-ui/elements/suggestions"
import { TooltipIconButton } from "@/components/assistant-ui/elements/tooltip-icon-button"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty"
import { useChat } from "@/hooks/use-chat"
import { earlierMessagesNote } from "@/lib/chat"
import { ChatInput } from "./ChatInput"
import { ChatMessageRow } from "./ChatMessageRow"

const SUGGESTIONS = ["List my items", "Add an item", "Show me Paris on the map"]

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
  const note = earlierMessagesNote(shown, total)

  return (
    <ThreadPrimitive.Root className="flex h-[calc(100svh-16rem)] min-h-96 flex-col gap-4">
      {isEmpty && !isRunning ? (
        <Empty className="flex-1">
          <EmptyHeader>
            <EmptyMedia variant="icon">
              <Sparkles />
            </EmptyMedia>
            <EmptyTitle>Start the conversation</EmptyTitle>
            <EmptyDescription>
              Ask anything, or try one of these
            </EmptyDescription>
          </EmptyHeader>
          <EmptyContent>
            <Suggestions
              suggestions={SUGGESTIONS}
              selectedSuggestion={null}
              cycle={0}
              onSuggestion={(suggestion) => void send(suggestion)}
            />
          </EmptyContent>
        </Empty>
      ) : (
        <div className="relative flex min-h-0 flex-1 flex-col">
          <ThreadPrimitive.Viewport
            turnAnchor="top"
            className="scroll-fade-b scrollbar-thin scrollbar-gutter-stable min-h-0 flex-1 overflow-y-auto overscroll-contain"
          >
            <div className="flex flex-col gap-3 pb-4">
              <ThreadPrimitive.Messages>
                {() => <ChatMessageRow />}
              </ThreadPrimitive.Messages>
            </div>
          </ThreadPrimitive.Viewport>
          <ThreadPrimitive.ScrollToBottom
            render={
              <TooltipIconButton
                tooltip="Scroll to bottom"
                variant="outline"
                className="absolute bottom-4 left-1/2 z-10 size-8 -translate-x-1/2 rounded-full bg-background transition-opacity disabled:pointer-events-none disabled:opacity-0"
              >
                <ArrowDown />
              </TooltipIconButton>
            }
          />
        </div>
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
    </ThreadPrimitive.Root>
  )
}
