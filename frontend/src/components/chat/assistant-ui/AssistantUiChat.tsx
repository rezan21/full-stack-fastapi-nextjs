"use client"

import {
  AssistantRuntimeProvider,
  AuiConfig,
  defineToolkit,
  ExportedMessageRepository,
  MessageByIndexProvider,
  MessagePrimitive,
  type ThreadMessage,
  Tools,
} from "@assistant-ui/react"
import { fromAgUiMessages, useAgUiRuntime } from "@assistant-ui/react-ag-ui"
import { useMemo, useRef, useState } from "react"
import { useAssistantUiChat } from "@/hooks/use-assistant-ui-chat"
import type { ChatMessage } from "@/lib/chat"
import { ChatAgent } from "@/lib/chat-agent"
import { CHAT_RUN_URL } from "@/lib/config"
import { LIST_ITEMS_TOOL } from "@/lib/items-tool"
import { FLY_TO_TOOL, flyTo, type Place, placeSchema } from "@/lib/place"
import type { ChatRow } from "../ChatMessageRow"
import { ChatWithMap } from "../ChatWithMap"
import { FlyToToolNote } from "../FlyToToolNote"
import { ItemsToolCard } from "../ItemsToolCard"

// Returns what a message says in text.
function textOf(message: ThreadMessage) {
  return message.content
    .flatMap((part) => (part.type === "text" ? [part.text] : []))
    .join("")
}

// Draws a message's tool calls.
function ToolCalls({ index }: { index: number }) {
  return (
    <MessageByIndexProvider index={index}>
      <MessagePrimitive.Parts components={{ Text: () => null }} />
    </MessageByIndexProvider>
  )
}

// Returns the rows to show: what was said, with the assistant's tool calls drawn under it.
function toRows(messages: readonly ThreadMessage[]): ChatRow[] {
  return messages.flatMap((message, index): ChatRow[] => {
    const content = textOf(message)
    if (message.role === "user") {
      return content ? [{ id: message.id, role: "user", content }] : []
    }
    const hasTools = message.content.some((part) => part.type === "tool-call")
    if (message.role !== "assistant" || (!content && !hasTools)) return []
    const tools = hasTools ? (
      <ToolCalls key={message.id} index={index} />
    ) : undefined
    return [{ id: message.id, role: "assistant", content, tools }]
  })
}

function Conversation({
  failure,
  shown,
  total,
  place,
}: {
  failure: React.RefObject<unknown>
  shown: number
  total: number
  place?: Place
}) {
  const chat = useAssistantUiChat(failure)
  return (
    <ChatWithMap
      chat={{ ...chat, messages: toRows(chat.messages) }}
      shown={shown}
      total={total}
      place={place}
    />
  )
}

// A conversation with the assistant, run through assistant-ui.
export function AssistantUiChat({
  conversationId,
  history,
  total,
}: {
  conversationId: string
  history: ChatMessage[]
  total: number
}) {
  const [place, setPlace] = useState<Place>()
  const [agent] = useState(
    () => new ChatAgent({ url: CHAT_RUN_URL, threadId: conversationId }),
  )
  const failure = useRef<unknown>(undefined)
  const toolkit = useMemo(
    () =>
      defineToolkit({
        [LIST_ITEMS_TOOL]: {
          type: "backend",
          render: ({ status, result }) => (
            <ItemsToolCard
              isDone={status.type === "complete"}
              result={result}
            />
          ),
        },
        [FLY_TO_TOOL]: {
          type: "frontend",
          description: "Move the map the user is looking at to a place.",
          parameters: placeSchema,
          execute: async (args) => flyTo(args, setPlace),
          render: ({ status, args }) => (
            <FlyToToolNote isDone={status.type === "complete"} place={args} />
          ),
        },
      }),
    [],
  )
  const config = useMemo(
    () => AuiConfig({ tools: Tools({ toolkit }) }),
    [toolkit],
  )
  const adapters = useMemo(
    () => ({
      history: {
        load: async () =>
          ExportedMessageRepository.fromArray(fromAgUiMessages(history)),
        append: async () => {},
      },
    }),
    [history],
  )
  const runtime = useAgUiRuntime({
    agent,
    adapters,
    onError: (error) => {
      failure.current = error
    },
  })

  return (
    <AssistantRuntimeProvider runtime={runtime} config={config}>
      <Conversation
        failure={failure}
        shown={history.length}
        total={total}
        place={place}
      />
    </AssistantRuntimeProvider>
  )
}
