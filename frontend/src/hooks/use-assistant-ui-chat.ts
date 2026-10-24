import { useAui, useAuiEvent, useAuiState } from "@assistant-ui/react"
import { type RefObject, useRef, useState } from "react"
import { chatErrorMessage, isRejection, isUnauthorized } from "@/lib/chat"

// Returns what the runtime reported as the run's failure.
function failureOf(ref: RefObject<unknown>) {
  return ref.current
}

// Runs a conversation with the assistant through assistant-ui; the runtime reports a failed run through the ref.
export function useAssistantUiChat(failure: RefObject<unknown>) {
  const aui = useAui()
  const messages = useAuiState((state) => state.thread.messages)
  const isRunning = useAuiState((state) => state.thread.isRunning)
  const [error, setError] = useState<string>()
  const runEnded = useRef<() => void>(undefined)
  const wasStopped = useRef(false)

  useAuiEvent("thread.runEnd", () => runEnded.current?.())

  const send = async (text: string): Promise<boolean> => {
    const known = new Set(
      aui
        .thread()
        .getState()
        .messages.map((m) => m.id),
    )
    failure.current = undefined
    wasStopped.current = false
    setError(undefined)
    const ended = new Promise<void>((resolve) => {
      runEnded.current = resolve
    })
    aui.thread().append({ role: "user", content: [{ type: "text", text }] })
    await ended

    const failed = failureOf(failure)
    if (!failed || wasStopped.current) return true
    if (isUnauthorized(failed)) window.location.assign("/login")
    else setError(chatErrorMessage(failed))
    if (!isRejection(failed)) return true
    const sent = aui
      .thread()
      .getState()
      .messages.find((m) => m.role === "user" && !known.has(m.id))
    if (sent) await aui.thread().deleteMessage(sent.id)
    return false
  }

  const stop = () => {
    wasStopped.current = true
    aui.thread().cancelRun()
  }

  return { messages, isRunning, error, send, stop }
}
