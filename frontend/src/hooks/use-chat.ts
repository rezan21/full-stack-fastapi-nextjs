import { randomUUID } from "@ag-ui/client"
import { useEffect, useState } from "react"
import {
  type ChatMessage,
  chatErrorMessage,
  isRejection,
  isUnauthorized,
  toChatMessages,
} from "@/lib/chat"
import { ChatAgent } from "@/lib/chat-agent"
import { CHAT_RUN_URL } from "@/lib/config"

// Runs a conversation with the assistant.
export function useChat(conversationId: string, history: ChatMessage[]) {
  const [agent] = useState(
    () =>
      new ChatAgent({
        url: CHAT_RUN_URL,
        threadId: conversationId,
        initialMessages: history,
      }),
  )
  const [messages, setMessages] = useState(history)
  const [isRunning, setIsRunning] = useState(false)
  const [error, setError] = useState<string>()

  useEffect(() => () => agent.abortRun(), [agent])

  const wasStopped = () => agent.abortController.signal.aborted

  const send = async (text: string): Promise<boolean> => {
    const id = randomUUID()
    let accepted = true
    setError(undefined)
    setIsRunning(true)
    try {
      agent.addMessage({ id, role: "user", content: text })
      setMessages(toChatMessages(agent.messages))
      await agent.runAgent(
        {},
        {
          onMessagesChanged: ({ messages }) =>
            setMessages(toChatMessages(messages)),
          onRunErrorEvent: ({ event }) => {
            if (!wasStopped()) setError(event.message)
          },
        },
      )
    } catch (e) {
      if (isRejection(e)) {
        accepted = false
        agent.setMessages(agent.messages.filter((message) => message.id !== id))
        setMessages(toChatMessages(agent.messages))
        if (isUnauthorized(e)) window.location.assign("/login")
        else setError(chatErrorMessage(e))
      } else if (!wasStopped()) {
        setError((current) => current ?? chatErrorMessage(e))
      }
    } finally {
      setIsRunning(false)
    }
    return accepted
  }

  return { messages, isRunning, error, send, stop: () => agent.abortRun() }
}
