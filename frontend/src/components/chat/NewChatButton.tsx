"use client"

import { Plus } from "lucide-react"
import { useRouter } from "next/navigation"
import { useTransition } from "react"
import { startConversation } from "@/actions/chat"
import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import { useCustomToast } from "@/hooks/use-custom-toast"

// Button that starts a new conversation.
export function NewChatButton() {
  const router = useRouter()
  const { showErrorToast } = useCustomToast()
  const [isPending, startTransition] = useTransition()

  const onClick = () =>
    startTransition(async () => {
      const { id, error } = await startConversation()
      if (!id) {
        showErrorToast(error ?? "Something went wrong.")
        return
      }
      router.push(`/chat/${id}`)
    })

  return (
    <Button onClick={onClick} disabled={isPending}>
      {isPending ? (
        <Spinner data-icon="inline-start" />
      ) : (
        <Plus data-icon="inline-start" />
      )}
      New chat
    </Button>
  )
}
