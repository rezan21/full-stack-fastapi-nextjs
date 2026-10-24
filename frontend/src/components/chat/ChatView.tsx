"use client"

import { useChat } from "@/hooks/use-chat"
import type { ChatMessage } from "@/lib/chat"
import { ChatPanel } from "./ChatPanel"

// A conversation with the assistant.
export function ChatView({
  conversationId,
  history,
  total,
}: {
  conversationId: string
  history: ChatMessage[]
  total: number
}) {
  const chat = useChat(conversationId, history)
  return <ChatPanel chat={chat} shown={history.length} total={total} />
}
