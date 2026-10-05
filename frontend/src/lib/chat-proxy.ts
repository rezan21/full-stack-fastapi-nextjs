import "server-only"
import { streamChat } from "@/lib/api"
import { chatRunSchema } from "@/lib/schemas"
import { deleteSession, getToken } from "@/lib/session"

export const MAX_BODY_BYTES = 64 * 1024

const UNTRANSFORMED = { "Cache-Control": "no-cache, no-transform" }
const FORWARDED_HEADERS = ["content-type", "retry-after"]

// Answers with a JSON reason.
function refuse(status: number, detail: string) {
  return Response.json({ detail }, { status, headers: UNTRANSFORMED })
}

// Returns whether the request comes from the app's own origin.
function isSameOrigin(request: Request) {
  const origin = request.headers.get("origin")
  if (!origin) return true
  const host =
    request.headers.get("x-forwarded-host") ?? request.headers.get("host")
  try {
    return new URL(origin).host === host
  } catch {
    return false
  }
}

// Returns the parsed JSON, or undefined when the text isn't JSON.
function parseJson(text: string): unknown {
  try {
    return JSON.parse(text)
  } catch {
    return undefined
  }
}

// Reads the request's JSON body, or returns the response that refuses it.
async function readRun(request: Request) {
  if (!request.headers.get("content-type")?.startsWith("application/json")) {
    return refuse(415, "Send JSON.")
  }
  const length = Number(request.headers.get("content-length") ?? 0)
  if (length > MAX_BODY_BYTES) return refuse(413, "The message is too large.")
  const text = await request.text()
  if (new TextEncoder().encode(text).length > MAX_BODY_BYTES) {
    return refuse(413, "The message is too large.")
  }
  const run = chatRunSchema.safeParse(parseJson(text))
  if (run.success) return run.data
  const [issue] = run.error.issues
  return refuse(
    400,
    issue?.code === "custom" ? issue.message : "That isn't a chat message.",
  )
}

// Starts a chat run for the signed-in user and streams the API's events back.
export async function proxyChatRun(request: Request): Promise<Response> {
  if (!isSameOrigin(request)) return refuse(403, "Forbidden.")
  if (!(await getToken())) return refuse(401, "Not authenticated.")
  const run = await readRun(request)
  if (run instanceof Response) return run

  let upstream: Response
  try {
    upstream = await streamChat(run, request.signal)
  } catch {
    return refuse(502, "The assistant is unavailable.")
  }
  if (upstream.status === 401) await deleteSession()

  const headers = new Headers(UNTRANSFORMED)
  for (const name of FORWARDED_HEADERS) {
    const value = upstream.headers.get(name)
    if (value) headers.set(name, value)
  }
  return new Response(upstream.body, { status: upstream.status, headers })
}
