import { beforeEach, describe, expect, test } from "bun:test"
import { API_URL } from "@/lib/config"
import {
  CONVERSATION,
  Redirect,
  resetServer,
  revalidated,
  session,
  stubFetch,
} from "@/test-support"

const { startConversation } = await import("@/actions/chat")

beforeEach(resetServer)

describe("startConversation", () => {
  test("sends a visitor without a session to login and asks nothing of the API", async () => {
    session.token = undefined
    const requests = stubFetch(() => Response.json(CONVERSATION))
    await expect(startConversation()).rejects.toEqual(new Redirect("/login"))
    expect(requests).toHaveLength(0)
  })

  test("ends a session the API rejects and goes to login", async () => {
    stubFetch(() =>
      Response.json(
        { detail: "Could not validate credentials" },
        { status: 401 },
      ),
    )
    await expect(startConversation()).rejects.toEqual(new Redirect("/login"))
    expect(session.token).toBeUndefined()
  })

  test("returns the API error and gives no conversation", async () => {
    stubFetch(() => Response.json({ detail: "Not yours." }, { status: 403 }))
    expect(await startConversation()).toEqual({
      error: "Not yours.",
      id: undefined,
    })
    expect(revalidated).toHaveLength(0)
  })

  test("returns the new conversation's id and refreshes the chat pages", async () => {
    const requests = stubFetch(() =>
      Response.json(CONVERSATION, { status: 201 }),
    )
    expect(await startConversation()).toEqual({ id: CONVERSATION.id })
    expect(revalidated).toEqual([["/chat", "layout"]])
    expect(requests[0]).toMatchObject({
      method: "POST",
      url: `${API_URL}/api/v1/chat/conversations`,
    })
  })

  test("a network failure becomes a generic error", async () => {
    stubFetch(() => {
      throw new TypeError("network down")
    })
    expect(await startConversation()).toEqual({
      error: "Something went wrong.",
      id: undefined,
    })
  })
})
