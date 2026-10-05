import { beforeEach, describe, expect, test } from "bun:test"
import { client } from "@/client/client.gen"
import { API_URL, CHAT_MESSAGE_MAX_LENGTH, ITEMS_PAGE_SIZE } from "@/lib/config"
import {
  CHAT_MESSAGES,
  CONVERSATION,
  ITEM,
  resetServer,
  stubFetch,
} from "@/test-support"

const {
  ApiError,
  CHAT_RUN_PATH,
  changePassword,
  completeSignup,
  confirmEmailChange,
  createConversation,
  createItem,
  deleteAccount,
  deleteItem,
  getConversation,
  getConversationMessages,
  getConversations,
  getCurrentUser,
  getItem,
  getItems,
  loginAccessToken,
  logout,
  recoverPassword,
  registerUser,
  requestEmailChange,
  resetPassword,
  streamChat,
  updateItem,
  updateProfile,
} = await import("@/lib/api")

const ITEM_ID = ITEM.id

beforeEach(resetServer)

async function failureOf(call: Promise<unknown>) {
  return call.then(
    () => {
      throw new Error("expected the call to fail")
    },
    (error: unknown) => error,
  )
}

describe("requests", () => {
  test("send the session token as a bearer token", async () => {
    const requests = stubFetch(() => Response.json({ data: [], count: 0 }))
    await getItems(1)
    expect(requests[0].authorization).toBe("Bearer test-token")
  })

  test("list the first page of items", async () => {
    const requests = stubFetch(() => Response.json({ data: [], count: 0 }))
    await getItems(1)
    expect(requests).toHaveLength(1)
    expect(requests[0].method).toBe("GET")
    expect(requests[0].url).toBe(
      `${API_URL}/api/v1/items?skip=0&limit=${ITEMS_PAGE_SIZE}`,
    )
  })

  test("skip the items on the earlier pages", async () => {
    const requests = stubFetch(() => Response.json({ data: [], count: 0 }))
    await getItems(3)
    expect(requests[0].url).toBe(
      `${API_URL}/api/v1/items?skip=${2 * ITEMS_PAGE_SIZE}&limit=${ITEMS_PAGE_SIZE}`,
    )
  })

  test("post a typed body as JSON", async () => {
    const requests = stubFetch(() => Response.json(ITEM, { status: 201 }))
    await createItem({ title: "A title", description: null })
    expect(requests[0].method).toBe("POST")
    expect(requests[0].contentType).toContain("application/json")
    expect(JSON.parse(requests[0].body)).toEqual({
      title: "A title",
      description: null,
    })
  })

  test("send the recovery address in the body, not the path", async () => {
    const requests = stubFetch(() => Response.json({ message: "sent" }))
    await recoverPassword({ email: "user@example.com" })
    expect(requests[0].url).toBe(`${API_URL}/api/v1/password-recovery`)
    expect(JSON.parse(requests[0].body)).toEqual({
      email: "user@example.com",
    })
  })

  test("send the login as a form", async () => {
    const requests = stubFetch(() =>
      Response.json({
        access_token: "t",
        token_type: "bearer",
        expires_in: 60,
      }),
    )
    await loginAccessToken("user@example.com", "a password")
    const form = new URLSearchParams(requests[0].body)
    expect(requests[0].contentType).toContain(
      "application/x-www-form-urlencoded",
    )
    expect(form.get("username")).toBe("user@example.com")
    expect(form.get("password")).toBe("a password")
  })

  test("return the parsed response", async () => {
    stubFetch(() => Response.json(ITEM))
    expect(await getItem(ITEM_ID)).toEqual(ITEM)
  })
})

describe("operations", () => {
  const cases: [string, () => Promise<unknown>, string, string][] = [
    ["getCurrentUser", () => getCurrentUser(), "GET", "/users/me"],
    ["logout", () => logout(), "POST", "/logout"],
    [
      "deleteAccount",
      () => deleteAccount({ current_password: "old-password" }),
      "DELETE",
      "/users/me",
    ],
    [
      "updateProfile",
      () => updateProfile({ full_name: "New Name" }),
      "PATCH",
      "/users/me",
    ],
    [
      "changePassword",
      () =>
        changePassword({
          current_password: "old",
          new_password: "password123",
        }),
      "PATCH",
      "/users/me/password",
    ],
    [
      "registerUser",
      () => registerUser({ email: "user@example.com", full_name: "A User" }),
      "POST",
      "/users/signup",
    ],
    [
      "completeSignup",
      () => completeSignup("a-token", "password123"),
      "POST",
      "/users/signup/complete",
    ],
    [
      "requestEmailChange",
      () =>
        requestEmailChange({
          email: "new@example.com",
          current_password: "old-password",
        }),
      "POST",
      "/users/me/email",
    ],
    [
      "confirmEmailChange",
      () => confirmEmailChange("a-token"),
      "POST",
      "/users/confirm-email",
    ],
    [
      "resetPassword",
      () => resetPassword("a-token", "password123"),
      "POST",
      "/reset-password",
    ],
    [
      "updateItem",
      () => updateItem(ITEM_ID, { title: "New title" }),
      "PATCH",
      `/items/${ITEM_ID}`,
    ],
    ["deleteItem", () => deleteItem(ITEM_ID), "DELETE", `/items/${ITEM_ID}`],
  ]

  for (const [name, call, method, path] of cases) {
    test(`${name} calls ${method} ${path}`, async () => {
      const requests = stubFetch(() => Response.json({}))
      await call()
      expect(requests).toHaveLength(1)
      expect(requests[0].method).toBe(method)
      expect(requests[0].url).toBe(`${API_URL}/api/v1${path}`)
    })
  }
})

describe("created and deleted resources", () => {
  test("a create returns the resource from a 201", async () => {
    stubFetch(() => Response.json(ITEM, { status: 201 }))
    expect(await createItem({ title: ITEM.title })).toEqual(ITEM)
  })

  const deletes: [string, () => Promise<unknown>][] = [
    ["deleteItem", () => deleteItem(ITEM_ID)],
    [
      "deleteAccount",
      () => deleteAccount({ current_password: "old-password" }),
    ],
  ]

  for (const [name, call] of deletes) {
    test(`${name} accepts a 204 with no body`, async () => {
      const requests = stubFetch(() => new Response(null, { status: 204 }))
      await call()
      expect(requests).toHaveLength(1)
    })
  }
})

describe("failures", () => {
  test("carry the backend's message and status", async () => {
    stubFetch(() =>
      Response.json({ detail: "Incorrect email or password" }, { status: 400 }),
    )
    const error = await failureOf(loginAccessToken("a@b.co", "wrong"))
    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({
      message: "Incorrect email or password",
      status: 400,
    })
  })

  test("use the first validation message from a 422", async () => {
    stubFetch(() =>
      Response.json(
        {
          detail: [
            { msg: "String should have at least 8 characters" },
            { msg: "another" },
          ],
        },
        { status: 422 },
      ),
    )
    const error = await failureOf(createItem({ title: "x" }))
    expect(error).toMatchObject({
      message: "String should have at least 8 characters",
      status: 422,
    })
  })

  test("use a plain-text body as the message", async () => {
    stubFetch(() => new Response("upstream down", { status: 502 }))
    expect(await failureOf(getItems(1))).toMatchObject({
      message: "upstream down",
      status: 502,
    })
  })

  test("fall back to the status text, then to a generic message", async () => {
    stubFetch(
      () =>
        new Response("", { status: 500, statusText: "Internal Server Error" }),
    )
    expect(await failureOf(getItems(1))).toMatchObject({
      message: "Internal Server Error",
    })
    stubFetch(() => new Response("", { status: 500 }))
    expect(await failureOf(getItems(1))).toMatchObject({
      message: "Something went wrong.",
    })
  })

  test("pass a network error through unchanged", async () => {
    stubFetch(() => {
      throw new TypeError("fetch failed")
    })
    const error = await failureOf(getItems(1))
    expect(error).toBeInstanceOf(TypeError)
    expect(error).not.toBeInstanceOf(ApiError)
  })
})

describe("request validation", () => {
  test("rejects an id that is not a UUID with a 422, without calling the API", async () => {
    const requests = stubFetch(() => Response.json({}))
    const error = await failureOf(getItem("not-a-uuid"))
    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ status: 422 })
    expect(requests).toHaveLength(0)
  })

  test("rejects a body that breaks the contract's rules", async () => {
    const requests = stubFetch(() => Response.json({}))
    const error = await failureOf(createItem({ title: "" }))
    expect(error).toMatchObject({ status: 422 })
    expect(requests).toHaveLength(0)
  })

  test("rejects an out-of-range page size", async () => {
    const requests = stubFetch(() => Response.json({}))
    const { itemsReadItems } = await import("@/client")
    const result = await itemsReadItems({ query: { limit: 101 } })
    expect(result.error).toBeDefined()
    expect(requests).toHaveLength(0)
  })
})

const CHAT_BASE = `${API_URL}/api/v1/chat`

describe("conversations", () => {
  test("createConversation posts to the conversations", async () => {
    const requests = stubFetch(() =>
      Response.json(CONVERSATION, { status: 201 }),
    )
    expect(await createConversation()).toEqual(CONVERSATION)
    expect(requests[0]).toMatchObject({
      method: "POST",
      url: `${CHAT_BASE}/conversations`,
      authorization: "Bearer test-token",
    })
  })

  test("getConversations lists them", async () => {
    const requests = stubFetch(() =>
      Response.json({ data: [CONVERSATION], count: 1 }),
    )
    expect(await getConversations()).toEqual({ data: [CONVERSATION], count: 1 })
    expect(requests[0]).toMatchObject({
      method: "GET",
      url: `${CHAT_BASE}/conversations`,
    })
  })

  test("getConversation reads one", async () => {
    const requests = stubFetch(() => Response.json(CONVERSATION))
    expect(await getConversation(CONVERSATION.id)).toEqual(CONVERSATION)
    expect(requests[0].url).toBe(
      `${CHAT_BASE}/conversations/${CONVERSATION.id}`,
    )
  })

  test("getConversationMessages reads what was said", async () => {
    const requests = stubFetch(() => Response.json(CHAT_MESSAGES))
    expect(await getConversationMessages(CONVERSATION.id)).toEqual(
      CHAT_MESSAGES,
    )
    expect(requests[0].url).toBe(
      `${CHAT_BASE}/conversations/${CONVERSATION.id}/messages`,
    )
  })

  test("an id that is not a UUID is refused without a request", async () => {
    const requests = stubFetch(() => Response.json({}))
    expect(await failureOf(getConversation("not-a-uuid"))).toMatchObject({
      status: 422,
    })
    expect(requests).toHaveLength(0)
  })

  test("the API's reason for refusing is kept", async () => {
    stubFetch(() =>
      Response.json({ detail: "Conversation not found" }, { status: 404 }),
    )
    expect(await failureOf(getConversation(CONVERSATION.id))).toMatchObject({
      status: 404,
      message: "Conversation not found",
    })
  })
})

describe("streamChat", () => {
  const body = {
    threadId: CONVERSATION.id,
    runId: "run-1",
    messages: [{ role: "user", content: "Hello" }],
  }
  const events = 'data: {"type":"RUN_STARTED"}\n\n'

  test("posts the run with the session token and hands back the stream untouched", async () => {
    const requests = stubFetch(
      () =>
        new Response(events, {
          headers: { "content-type": "text/event-stream" },
        }),
    )
    const response = await streamChat(body, new AbortController().signal)
    expect(requests[0]).toMatchObject({
      method: "POST",
      url: CHAT_BASE,
      authorization: "Bearer test-token",
    })
    expect(requests[0].contentType).toContain("application/json")
    expect(JSON.parse(requests[0].body)).toEqual(body)
    expect(response.status).toBe(200)
    expect(response.headers.get("content-type")).toContain("text/event-stream")
    expect(await response.text()).toBe(events)
  })

  test("keeps the status, the reason and the retry delay of a refusal", async () => {
    stubFetch(() =>
      Response.json(
        { detail: "Too many messages. Try again in 1 hour." },
        { status: 429, headers: { "retry-after": "1800" } },
      ),
    )
    const response = await streamChat(body, new AbortController().signal)
    expect(response.status).toBe(429)
    expect(response.headers.get("retry-after")).toBe("1800")
    expect(await response.json()).toEqual({
      detail: "Too many messages. Try again in 1 hour.",
    })
  })

  test("fails when the API cannot be reached", async () => {
    stubFetch(() => {
      throw new TypeError("network down")
    })
    expect(
      await failureOf(streamChat(body, new AbortController().signal)),
    ).toBeInstanceOf(TypeError)
  })

  test("passes the caller's abort signal on to the request", async () => {
    const controller = new AbortController()
    let seen: AbortSignal | null | undefined
    client.setConfig({
      fetch: Object.assign(
        async (input: RequestInfo | URL, init?: RequestInit) => {
          seen = new Request(input, init).signal
          return new Response(events)
        },
        { preconnect: () => {} },
      ),
    })
    await streamChat(body, controller.signal)
    controller.abort()
    expect(seen?.aborted).toBe(true)
  })

  test("allows as long a message as the API publishes", async () => {
    const spec = await Bun.file(
      new URL("../../../backend/openapi.json", import.meta.url),
    ).json()
    expect(
      spec.components.schemas.ChatRun.properties.messages[
        "x-max-user-message-length"
      ],
    ).toBe(CHAT_MESSAGE_MAX_LENGTH)
  })

  test("goes to the path the generated contract documents", async () => {
    const spec = await Bun.file(
      new URL("../../../backend/openapi.json", import.meta.url),
    ).json()
    expect(spec.paths[CHAT_RUN_PATH].post.operationId).toBe("chat-run_chat")
  })
})
