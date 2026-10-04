import "server-only"
import { ApiError } from "@/lib/api"

export type ActionResult = { error?: string }

// Converts a thrown error into an action result.
export function toError(e: unknown): ActionResult {
  return { error: e instanceof ApiError ? e.message : "Something went wrong." }
}
