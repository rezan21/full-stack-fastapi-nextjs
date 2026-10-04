import "server-only"
import { notFound } from "next/navigation"
import { cache } from "react"
import { ApiError, getCurrentUser, getItem, type UserPublic } from "@/lib/api"
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

// Loads an item, or renders not-found when it isn't available.
export async function loadItem(id: string) {
  try {
    return await getItem(id)
  } catch (e) {
    if (e instanceof ApiError && NOT_FOUND_STATUSES.includes(e.status)) {
      notFound()
    }
    throw e
  }
}
