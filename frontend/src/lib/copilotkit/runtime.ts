import "server-only"
import {
  CopilotRuntime,
  type CopilotRuntimeHooks,
  createCopilotRuntimeHandler,
} from "@copilotkit/runtime/v2"
import { ApiError, getConversation } from "@/lib/api"
import { CHAT_AGENT_ID, COPILOT_RUNTIME_URL } from "@/lib/config"
import { createChatAgent } from "@/lib/copilotkit/agent"
import { ChatRunner } from "@/lib/copilotkit/runner"
import { getToken } from "@/lib/session"

export const MAX_BODY_BYTES = 64 * 1024

const NOT_FOUND_STATUSES = [403, 404, 422]

// Answers with a JSON reason.
function refuse(status: number, detail: string) {
  return Response.json({ detail }, { status })
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

// Throws the response that refuses a body that isn't small JSON.
async function checkBody(request: Request) {
  if (!request.headers.get("content-type")?.startsWith("application/json")) {
    throw refuse(415, "Send JSON.")
  }
  const length = Number(request.headers.get("content-length") ?? 0)
  const text = length > MAX_BODY_BYTES ? "" : await request.text()
  if (
    length > MAX_BODY_BYTES ||
    new TextEncoder().encode(text).length > MAX_BODY_BYTES
  ) {
    throw refuse(413, "The message is too large.")
  }
}

// Throws the response that refuses a conversation that isn't the user's.
async function checkOwner(conversationId: string) {
  try {
    await getConversation(conversationId)
  } catch (e) {
    const status = e instanceof ApiError ? e.status : 502
    if (status === 401) throw refuse(401, "Not authenticated.")
    if (NOT_FOUND_STATUSES.includes(status)) throw refuse(404, "Not found.")
    throw refuse(502, "The assistant is unavailable.")
  }
}

const hooks: CopilotRuntimeHooks = {
  onRequest: async ({ request }) => {
    if (!isSameOrigin(request)) throw refuse(403, "Forbidden.")
    if (!(await getToken())) throw refuse(401, "Not authenticated.")
    if (request.method === "POST") await checkBody(request.clone())
  },
  onBeforeHandler: async ({ route }) => {
    if (route.method === "info") return
    if (route.method === "agent/run" && route.agentId === CHAT_AGENT_ID) return
    if (route.method === "agent/stop" && route.agentId === CHAT_AGENT_ID) {
      return checkOwner(route.threadId)
    }
    throw refuse(404, "Not found.")
  },
}

const runtime = new CopilotRuntime({
  agents: { [CHAT_AGENT_ID]: createChatAgent() },
  runner: new ChatRunner(),
})

export const copilotHandler = createCopilotRuntimeHandler({
  runtime,
  basePath: COPILOT_RUNTIME_URL,
  hooks,
})
