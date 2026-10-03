import "server-only"
import { ApiError } from "@/lib/api"

export type ActionResult = { error?: string }

export function toError(e: unknown): ActionResult {
  return { error: e instanceof ApiError ? e.message : "Something went wrong." }
}
