"use server"

import { revalidatePath } from "next/cache"
import { type ActionResult, authenticated } from "@/lib/action-result"
import { createConversation } from "@/lib/api"

// Starts a conversation.
export async function startConversation(): Promise<
  ActionResult & { id?: string }
> {
  let id: string | undefined
  const result = await authenticated(async () => {
    id = (await createConversation()).id
    revalidatePath("/chat", "layout")
  })
  return { ...result, id }
}
