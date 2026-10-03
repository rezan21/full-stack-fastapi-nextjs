import "server-only"
import { notFound } from "next/navigation"
import { cache } from "react"
import { ApiError, getCurrentUser, getItem, type UserPublic } from "@/lib/api"
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

const NOT_FOUND_STATUSES = [403, 404, 422]

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
