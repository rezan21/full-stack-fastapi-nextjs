import "server-only"
import { notFound } from "next/navigation"
import { cache } from "react"
import {
  ApiError,
  getConversation,
  getConversationMessages,
  getCurrentUser,
  getItem,
  type UserPublic,
} from "@/lib/api"
import { getToken } from "@/lib/session"

// Returns the current user, or null when there is no valid session.
export const getUser = cache(async (): Promise<UserPublic | null> => {
  const token = await getToken()
  if (!token) return null
  try {
    return await getCurrentUser()
  } catch (e) {
    if (e instanceof ApiError && e.status === 401) return null
    throw e
  }
})

const NOT_FOUND_STATUSES = [403, 404, 422]

// Runs a load, rendering not-found when the API says the resource isn't available.
async function orNotFound<T>(load: () => Promise<T>): Promise<T> {
  try {
    return await load()
  } catch (e) {
    if (e instanceof ApiError && NOT_FOUND_STATUSES.includes(e.status)) {
      notFound()
    }
    throw e
  }
}

// Loads an item, or renders not-found when it isn't available.
export function loadItem(id: string) {
  return orNotFound(() => getItem(id))
}

// Loads a conversation, or renders not-found when it isn't the user's.
export function loadConversation(id: string) {
  return orNotFound(() => getConversation(id))
}

// Loads a conversation's transcript, or renders not-found when it isn't the user's.
export function loadMessages(id: string) {
  return orNotFound(() => getConversationMessages(id))
}
