"use client"

import type { Message } from "@ag-ui/client"
import { CopilotKitProvider } from "@copilotkit/react-core/v2"
import { useRenderToolCall } from "@copilotkit/react-core/v2/headless"
import { Fragment, useState } from "react"
import { useCopilotKitChat } from "@/hooks/use-copilotkit-chat"
import { type ChatMessage, toChatMessages } from "@/lib/chat"
import { COPILOT_RUNTIME_URL } from "@/lib/config"
import type { Place } from "@/lib/place"
import type { ChatRow } from "../ChatMessageRow"
import { ChatWithMap } from "../ChatWithMap"
import { CopilotKitTools } from "./CopilotKitTools"

const newestMessageOnly = (messages: Message[]) => messages.slice(-1)

type RenderToolCall = ReturnType<typeof useRenderToolCall>

// Returns the rows to show: what was said, with the assistant's tool calls drawn under it.
function toRows(
  messages: readonly Message[],
  renderToolCall: RenderToolCall,
): ChatRow[] {
  const answers = new Map(
    messages.flatMap((message) =>
      message.role === "tool" ? [[message.toolCallId, message] as const] : [],
    ),
  )
  return messages.flatMap((message) => {
    if (message.role === "assistant" && message.toolCalls?.length) {
      const [said] = toChatMessages([message])
      const tools = message.toolCalls.map((toolCall) => (
        <Fragment key={toolCall.id}>
          {renderToolCall({ toolCall, toolMessage: answers.get(toolCall.id) })}
        </Fragment>
      ))
      return [
        {
          ...(said ?? { id: message.id, role: "assistant", content: "" }),
          tools,
        },
      ]
    }
    return toChatMessages([message])
  })
}

function Conversation({
  conversationId,
  history,
  total,
}: {
  conversationId: string
  history: ChatMessage[]
  total: number
}) {
  const [place, setPlace] = useState<Place>()
  const chat = useCopilotKitChat(conversationId, history)
  const renderToolCall = useRenderToolCall()
  const rows = toRows(chat.messages, renderToolCall)

  return (
    <>
      <CopilotKitTools onFlyTo={setPlace} />
      <ChatWithMap
        chat={{ ...chat, messages: rows }}
        shown={history.length}
        total={total}
        place={place}
      />
    </>
  )
}

// A conversation with the assistant, run through CopilotKit.
export function CopilotKitChat(props: {
  conversationId: string
  history: ChatMessage[]
  total: number
}) {
  return (
    <CopilotKitProvider
      runtimeUrl={COPILOT_RUNTIME_URL}
      useSingleEndpoint={false}
      messageFilter={newestMessageOnly}
      enableInspector={false}
    >
      <Conversation {...props} />
    </CopilotKitProvider>
  )
}
