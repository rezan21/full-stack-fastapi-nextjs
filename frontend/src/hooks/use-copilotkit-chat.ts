import { type Message, randomUUID } from "@ag-ui/client"
import { useAgent, useCopilotKit } from "@copilotkit/react-core/v2/headless"
import { useEffect, useRef, useState } from "react"
import { type ChatMessage, GENERIC_CHAT_ERROR, refusalStatus } from "@/lib/chat"
import { CHAT_AGENT_ID } from "@/lib/config"

type Failure = { message: string; code?: string }

// Returns what the run's error handlers recorded.
function failureOf(ref: { current: Failure | undefined }) {
  return ref.current
}

// Runs a conversation with the assistant through CopilotKit.
export function useCopilotKitChat(
  conversationId: string,
  history: ChatMessage[],
) {
  const { agent, isReady } = useAgent({
    agentId: `${CHAT_AGENT_ID}-${conversationId}`,
    runtimeAgentId: CHAT_AGENT_ID,
    threadId: conversationId,
  })
  const { copilotkit } = useCopilotKit()
  const [error, setError] = useState<string>()
  const failure = useRef<Failure>(undefined)
  const wasStopped = useRef(false)

  useEffect(() => {
    if (isReady) agent.setMessages(history)
  }, [agent, isReady, history])

  useEffect(() => {
    const subscription = agent.subscribe({
      onRunErrorEvent: ({ event }) => {
        failure.current = { message: event.message, code: event.code }
      },
      onRunFailed: () => {
        failure.current = { message: GENERIC_CHAT_ERROR }
      },
    })
    return () => subscription.unsubscribe()
  }, [agent])

  useEffect(() => () => agent.abortRun(), [agent])

  const send = async (text: string): Promise<boolean> => {
    const id = randomUUID()
    failure.current = undefined
    wasStopped.current = false
    setError(undefined)
    agent.addMessage({ id, role: "user", content: text })
    await copilotkit.runAgent({ agent })

    const failed = failureOf(failure)
    if (!failed || wasStopped.current) return true
    const status = refusalStatus(failed.code)
    if (status === 401) window.location.assign("/login")
    else setError(failed.message)
    if (status === undefined) return true
    agent.setMessages(agent.messages.filter((message) => message.id !== id))
    return false
  }

  const stop = () => {
    wasStopped.current = true
    copilotkit.stopAgent({ agent })
  }

  const messages: readonly Message[] =
    agent.messages.length > 0 ? agent.messages : history
  return { messages, isRunning: agent.isRunning, error, send, stop }
}
