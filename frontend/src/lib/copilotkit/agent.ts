import "server-only"
import { EventType, HttpAgent, type HttpAgentFetchFn } from "@ag-ui/client"
import { filter } from "rxjs"
import { CHAT_RUN_PATH, streamChat } from "@/lib/api"
import { chatRunSchema } from "@/lib/schemas"

// Answers with a JSON reason, the shape the API uses for a refusal.
function refuse(status: number, detail: string) {
  return Response.json({ detail }, { status })
}

// Sends the newest message to the API and returns its stream, or a refusal.
const postRun: HttpAgentFetchFn = async (_url, init) => {
  const run = chatRunSchema.safeParse(JSON.parse(String(init.body)))
  if (!run.success) {
    const [issue] = run.error.issues
    return refuse(
      400,
      issue?.code === "custom" ? issue.message : "That isn't a chat message.",
    )
  }
  try {
    return await streamChat(
      { ...run.data, messages: run.data.messages.slice(-1) },
      init.signal ?? undefined,
    )
  } catch {
    return refuse(502, "The assistant is unavailable.")
  }
}

// Creates the agent that runs a chat message through the API.
export function createChatAgent() {
  const agent = new HttpAgent({ url: CHAT_RUN_PATH, fetch: postRun })
  agent.use((input, next) =>
    next
      .run(input)
      .pipe(filter((event) => event.type !== EventType.MESSAGES_SNAPSHOT)),
  )
  return agent
}
