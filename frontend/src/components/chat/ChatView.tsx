"use client"

import {
  AssistantRuntimeProvider,
  AuiConfig,
  defineToolkit,
  ExportedMessageRepository,
  Tools,
} from "@assistant-ui/react"
import { fromAgUiMessages, useAgUiRuntime } from "@assistant-ui/react-ag-ui"
import { useMemo, useState } from "react"
import { type ChatMessage, chatErrorMessage, isUnauthorized } from "@/lib/chat"
import { ChatAgent } from "@/lib/chat-agent"
import { CHAT_RUN_URL } from "@/lib/config"
import type { Place } from "@/lib/place-tool"
import { ChatPanel } from "./ChatPanel"
import { itemsToolkit } from "./items/items-toolkit"
import { PlaceMap } from "./place/PlaceMap"
import { placeToolkit } from "./place/place-toolkit"

// A conversation with the assistant, beside the map it can move.
export function ChatView({
  conversationId,
  history,
  total,
}: {
  conversationId: string
  history: ChatMessage[]
  total: number
}) {
  const [place, setPlace] = useState<Place>()
  const [error, setError] = useState<string>()
  const [agent] = useState(
    () => new ChatAgent({ url: CHAT_RUN_URL, threadId: conversationId }),
  )
  const config = useMemo(
    () =>
      AuiConfig({
        tools: Tools({
          toolkit: defineToolkit({
            ...itemsToolkit,
            ...placeToolkit(setPlace),
          }),
        }),
      }),
    [],
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
    resumeTranscript: "appended",
    onError: (failure) => {
      if (isUnauthorized(failure)) window.location.assign("/login")
      else setError(chatErrorMessage(failure))
    },
  })

  return (
    <AssistantRuntimeProvider runtime={runtime} config={config}>
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <ChatPanel
          error={error}
          clearError={() => setError(undefined)}
          shown={history.length}
          total={total}
        />
        <PlaceMap place={place} />
      </div>
    </AssistantRuntimeProvider>
  )
}
