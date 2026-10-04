import "server-only"
import { redirect } from "next/navigation"
import { ApiError } from "@/lib/api"
import { deleteSession, getToken } from "@/lib/session"

export type ActionResult = { error?: string }

// Converts a thrown error into an action result.
function toError(e: unknown): ActionResult {
  return { error: e instanceof ApiError ? e.message : "Something went wrong." }
}

// Runs an action and turns a thrown error into a result.
export async function attempt(
  run: () => Promise<unknown>,
): Promise<ActionResult> {
  try {
    await run()
    return {}
  } catch (e) {
    return toError(e)
  }
}

// Runs an action for a signed-in user, sending anyone without a valid session to the login page.
export async function authenticated(
  run: () => Promise<unknown>,
): Promise<ActionResult> {
  if (!(await getToken())) redirect("/login")
  try {
    await run()
    return {}
  } catch (e) {
    if (e instanceof ApiError && e.status === 401) {
      await deleteSession()
      redirect("/login")
    }
    return toError(e)
  }
}
