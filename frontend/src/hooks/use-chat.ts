import { useAui } from "@assistant-ui/react"
import { useAgUiSteerAway } from "@assistant-ui/react-ag-ui"
import { isRejection } from "@/lib/chat"

// Sends and stops a conversation's runs; a refused message is taken back out of the thread.
export function useChat(clearError: () => void) {
  const aui = useAui()
  const steerAway = useAgUiSteerAway()

  const send = async (text: string): Promise<boolean> => {
    clearError()
    try {
      await steerAway(text)
      return true
    } catch (failure) {
      if (!isRejection(failure)) return true
      const sent = aui
        .thread()
        .getState()
        .messages.findLast((message) => message.role === "user")
      if (sent) await aui.thread().deleteMessage(sent.id)
      return false
    }
  }

  const stop = () => aui.thread().cancelRun()

  return { send, stop }
}
