import "server-only"
import { cache } from "react"
import { getCurrentUser, type UserPublic } from "@/lib/api"
import { getToken } from "@/lib/session"

export const getUser = cache(async (): Promise<UserPublic | null> => {
  const token = await getToken()
  if (!token) return null
  try {
    return await getCurrentUser()
  } catch {
    return null
  }
})
