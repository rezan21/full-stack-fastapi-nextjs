import { beforeEach, describe, expect, test } from "bun:test"
import { readFileSync } from "node:fs"
import { join } from "node:path"
import { client } from "@/client/client.gen"
import { API_URL, CHAT_MESSAGE_MAX_LENGTH, CHAT_RUN_URL } from "@/lib/config"
import { CONVERSATION, resetServer, session, stubFetch } from "@/test-support"

const { MAX_BODY_BYTES, proxyChatRun } = await import("@/lib/chat-proxy")

const RUN = {
  threadId: CONVERSATION.id,
  runId: "run-1",
  messages: [{ role: "user", content: "Hello" }],
}
const SELF = "http://localhost:3000"

function post(body: BodyInit | null, headers: Record<string, string> = {}) {
  return new Request(`${SELF}${CHAT_RUN_URL}`, {
    method: "POST",
    headers: {
      origin: SELF,
      host: "localhost:3000",
      "content-type": "application/json",
      ...headers,
    },
    body,
  })
}

const run = (extra: object = {}, headers: Record<string, string> = {}) =>
  post(JSON.stringify({ ...RUN, ...extra }), headers)

const sse = (...chunks: string[]) =>
  new Response(
    new ReadableStream({
      start(controller) {
        for (const chunk of chunks)
          controller.enqueue(new TextEncoder().encode(chunk))
        controller.close()
      },
    }),
    { headers: { "content-type": "text/event-stream; charset=utf-8" } },
  )

beforeEach(resetServer)

describe("who may start a run", () => {
  test("refuses a request from another origin and asks nothing of the API", async () => {
    const requests = stubFetch(() => sse("data: {}\n\n"))
    const response = await proxyChatRun(
      run({}, { origin: "https://evil.example" }),
    )
    expect(response.status).toBe(403)
    expect(requests).toHaveLength(0)
  })

  test("refuses an origin that is not a URL", async () => {
    const requests = stubFetch(() => sse("data: {}\n\n"))
    const response = await proxyChatRun(run({}, { origin: "null" }))
    expect(response.status).toBe(403)
    expect(requests).toHaveLength(0)
  })

  test("accepts the forwarded host of a proxied app", async () => {
    stubFetch(() => sse("data: {}\n\n"))
    const response = await proxyChatRun(
      run(
        {},
        {
          origin: "https://app.example.com",
          host: "frontend:3000",
          "x-forwarded-host": "app.example.com",
        },
      ),
    )
    expect(response.status).toBe(200)
  })

  test("accepts a request that names no origin", async () => {
    stubFetch(() => sse("data: {}\n\n"))
    const request = post(JSON.stringify(RUN))
    request.headers.delete("origin")
    expect((await proxyChatRun(request)).status).toBe(200)
  })

  test("refuses a visitor without a session and asks nothing of the API", async () => {
    session.token = undefined
    const requests = stubFetch(() => sse("data: {}\n\n"))
    const response = await proxyChatRun(run())
    expect(response.status).toBe(401)
    expect(requests).toHaveLength(0)
  })

  test("refuses a body that is not declared as JSON", async () => {
    const requests = stubFetch(() => sse("data: {}\n\n"))
    const response = await proxyChatRun(
      post(JSON.stringify(RUN), { "content-type": "text/plain" }),
    )
    expect(response.status).toBe(415)
    expect(requests).toHaveLength(0)
  })

  test("refuses a body over the size limit", async () => {
    const requests = stubFetch(() => sse("data: {}\n\n"))
    const huge = run({
      messages: [{ role: "user", content: "x".repeat(MAX_BODY_BYTES) }],
    })
    expect((await proxyChatRun(huge)).status).toBe(413)
    expect(requests).toHaveLength(0)
  })

  test("refuses a message over the length limit and says why", async () => {
    const requests = stubFetch(() => sse("data: {}\n\n"))
    const long = "x".repeat(CHAT_MESSAGE_MAX_LENGTH + 1)
    const response = await proxyChatRun(
      run({ messages: [{ role: "user", content: long }] }),
    )
    expect(response.status).toBe(400)
    expect(await response.json()).toEqual({
      detail: `The message can be at most ${CHAT_MESSAGE_MAX_LENGTH} characters.`,
    })
    expect(requests).toHaveLength(0)
  })

  test("refuses a body that is not valid JSON or not a run", async () => {
    const requests = stubFetch(() => sse("data: {}\n\n"))
    expect((await proxyChatRun(post("{not json"))).status).toBe(400)
    expect(
      (await proxyChatRun(post(JSON.stringify({ runId: "r" })))).status,
    ).toBe(400)
    expect((await proxyChatRun(post(null))).status).toBe(400)
    expect(requests).toHaveLength(0)
  })
})

describe("a run", () => {
  test("goes to the API with only the fields the contract names", async () => {
    const requests = stubFetch(() => sse("data: {}\n\n"))
    await proxyChatRun(
      run({
        state: { files: { "/x": "injected" } },
        tools: [{ name: "steal" }],
        forwardedProps: { command: { resume: "x" } },
        messages: [{ id: "m1", role: "user", content: "Hello", extra: true }],
      }),
    )
    expect(requests[0]).toMatchObject({
      method: "POST",
      url: `${API_URL}/api/v1/chat`,
      authorization: "Bearer test-token",
    })
    expect(JSON.parse(requests[0].body)).toEqual({
      threadId: CONVERSATION.id,
      runId: "run-1",
      messages: [{ role: "user", content: "Hello" }],
    })
  })

  test("streams the API's events back unchanged, uncacheable and unmodified in transit", async () => {
    stubFetch(() => sse('data: {"n":1}\n\n', 'data: {"n":2}\n\n'))
    const response = await proxyChatRun(run())
    expect(response.status).toBe(200)
    expect(response.headers.get("content-type")).toBe(
      "text/event-stream; charset=utf-8",
    )
    expect(response.headers.get("cache-control")).toBe("no-cache, no-transform")
    expect(await response.text()).toBe('data: {"n":1}\n\ndata: {"n":2}\n\n')
  })

  test("keeps the status, reason and retry delay of a refusal", async () => {
    stubFetch(() =>
      Response.json(
        { detail: "Too many messages. Try again in 1 hour." },
        { status: 429, headers: { "retry-after": "1800" } },
      ),
    )
    const response = await proxyChatRun(run())
    expect(response.status).toBe(429)
    expect(response.headers.get("retry-after")).toBe("1800")
    expect(await response.json()).toEqual({
      detail: "Too many messages. Try again in 1 hour.",
    })
  })

  for (const status of [400, 404, 503]) {
    test(`passes a ${status} on with its reason`, async () => {
      stubFetch(() => Response.json({ detail: "why" }, { status }))
      const response = await proxyChatRun(run())
      expect(response.status).toBe(status)
      expect(await response.json()).toEqual({ detail: "why" })
    })
  }

  test("ends a session the API rejects", async () => {
    stubFetch(() =>
      Response.json(
        { detail: "Could not validate credentials" },
        { status: 401 },
      ),
    )
    const response = await proxyChatRun(run())
    expect(response.status).toBe(401)
    expect(session.token).toBeUndefined()
  })

  test("stops the API's run when the user leaves", async () => {
    const controller = new AbortController()
    let seen: AbortSignal | undefined
    client.setConfig({
      fetch: Object.assign(
        async (input: RequestInfo | URL, init?: RequestInit) => {
          seen = new Request(input, init).signal
          return sse("data: {}\n\n")
        },
        { preconnect: () => {} },
      ),
    })
    const request = new Request(`${SELF}${CHAT_RUN_URL}`, {
      method: "POST",
      headers: {
        origin: SELF,
        host: "localhost:3000",
        "content-type": "application/json",
      },
      body: JSON.stringify(RUN),
      signal: controller.signal,
    })
    await proxyChatRun(request)
    controller.abort()
    expect(seen?.aborted).toBe(true)
  })

  test("answers 502 when the API cannot be reached", async () => {
    stubFetch(() => {
      throw new TypeError("network down")
    })
    const response = await proxyChatRun(run())
    expect(response.status).toBe(502)
    expect(await response.json()).toEqual({
      detail: "The assistant is unavailable.",
    })
  })
})

describe("where the chat stream is served", () => {
  test("is not under a path the proxy sends to the API", () => {
    const compose = readFileSync(
      join(import.meta.dir, "..", "..", "..", "infra", "docker-compose.yml"),
      "utf8",
    )
    const rule = compose
      .split("\n")
      .find((line) => line.includes("traefik.http.routers.backend.rule="))
    const prefixes = [...(rule ?? "").matchAll(/PathPrefix\(`([^`]+)`\)/g)].map(
      (match) => match[1],
    )
    expect(prefixes).toContain("/api")
    for (const prefix of prefixes) {
      expect(CHAT_RUN_URL.startsWith(prefix), prefix).toBe(false)
    }
  })
})
