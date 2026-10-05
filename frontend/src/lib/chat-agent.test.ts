import { describe, expect, test } from "bun:test"
import { ChatAgent } from "@/lib/chat-agent"
import { CHAT_RUN_URL } from "@/lib/config"

const stream = (...events: object[]) =>
  new Response(events.map((e) => `data: ${JSON.stringify(e)}\n\n`).join(""), {
    headers: { "content-type": "text/event-stream" },
  })

const answer = (text: string) =>
  stream(
    { type: "RUN_STARTED", threadId: "t-1", runId: "r-1" },
    { type: "TEXT_MESSAGE_START", messageId: "a-2", role: "assistant" },
    { type: "TEXT_MESSAGE_CONTENT", messageId: "a-2", delta: text },
    { type: "TEXT_MESSAGE_END", messageId: "a-2" },
    { type: "RUN_FINISHED", threadId: "t-1", runId: "r-1" },
  )

function agentThatRecords(reply: () => Response) {
  const sent: Record<string, unknown>[] = []
  const agent = new ChatAgent({
    url: CHAT_RUN_URL,
    threadId: "t-1",
    initialMessages: [
      { id: "u-1", role: "user", content: "an old question" },
      { id: "a-1", role: "assistant", content: "an old answer" },
    ],
    initialState: { files: { "/notes.txt": "a lot of stored text" } },
    fetch: async (_url, init) => {
      sent.push(JSON.parse(String(init.body)))
      return reply()
    },
  })
  return { agent, sent }
}

describe("ChatAgent", () => {
  test("sends only the newest message and none of the stored state", async () => {
    const { agent, sent } = agentThatRecords(() => answer("Hi"))
    agent.addMessage({ id: "u-2", role: "user", content: "a new question" })

    await agent.runAgent()

    expect(sent).toHaveLength(1)
    expect(sent[0].threadId).toBe("t-1")
    expect(sent[0].messages).toEqual([
      { id: "u-2", role: "user", content: "a new question" },
    ])
    expect(sent[0].state).toEqual({})
  })

  test("keeps sending only the newest message after earlier runs", async () => {
    const { agent, sent } = agentThatRecords(() => answer("Hi"))
    agent.addMessage({ id: "u-2", role: "user", content: "first" })
    await agent.runAgent()
    agent.addMessage({ id: "u-3", role: "user", content: "second" })

    await agent.runAgent()

    expect(sent[1].messages).toEqual([
      { id: "u-3", role: "user", content: "second" },
    ])
  })

  test("applies the streamed answer to the conversation", async () => {
    const { agent } = agentThatRecords(() => answer("Hello there"))
    agent.addMessage({ id: "u-2", role: "user", content: "a new question" })

    await agent.runAgent()

    const last = agent.messages.at(-1)
    expect(last).toMatchObject({ role: "assistant", content: "Hello there" })
  })

  test("keeps the conversation in order when the server's snapshot names the user's message differently", async () => {
    const { agent } = agentThatRecords(() =>
      stream(
        { type: "RUN_STARTED", threadId: "t-1", runId: "r-1" },
        { type: "TEXT_MESSAGE_START", messageId: "a-2", role: "assistant" },
        { type: "TEXT_MESSAGE_CONTENT", messageId: "a-2", delta: "Hello" },
        { type: "TEXT_MESSAGE_END", messageId: "a-2" },
        {
          type: "MESSAGES_SNAPSHOT",
          messages: [
            { id: "u-1", role: "user", content: "an old question" },
            { id: "a-1", role: "assistant", content: "an old answer" },
            { id: "server-made-id", role: "user", content: "a new question" },
            { id: "a-2", role: "assistant", content: "Hello" },
          ],
        },
        { type: "RUN_FINISHED", threadId: "t-1", runId: "r-1" },
      ),
    )
    agent.addMessage({ id: "u-2", role: "user", content: "a new question" })

    await agent.runAgent()

    expect(agent.messages.map((m) => `${m.role}:${m.id}`)).toEqual([
      "user:u-1",
      "assistant:a-1",
      "user:u-2",
      "assistant:a-2",
    ])
  })

  test("fails with the API's status and reason when it refuses", async () => {
    const { agent } = agentThatRecords(() =>
      Response.json({ detail: "Too many messages." }, { status: 429 }),
    )
    agent.addMessage({ id: "u-2", role: "user", content: "again" })

    const error = await agent.runAgent().catch((e: unknown) => e)

    expect(error).toMatchObject({
      status: 429,
      payload: { detail: "Too many messages." },
    })
  })
})
