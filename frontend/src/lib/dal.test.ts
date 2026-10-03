import { beforeEach, describe, expect, test } from "bun:test"
import { ITEM, NotFound, session, stubFetch, USER } from "@/test-support"

const { ApiError } = await import("@/lib/api")
const { getUser, loadItem } = await import("@/lib/dal")

const ITEM_ID = ITEM.id

beforeEach(() => {
  session.token = "test-token"
})

describe("loadItem", () => {
  test("returns the item", async () => {
    stubFetch(() => Response.json(ITEM))
    expect(await loadItem(ITEM_ID)).toEqual(ITEM)
  })

  for (const status of [403, 404, 422]) {
    test(`shows not found for a ${status}`, async () => {
      stubFetch(() => Response.json({ detail: "nope" }, { status }))
      await expect(loadItem(ITEM_ID)).rejects.toBeInstanceOf(NotFound)
    })
  }

  test("shows not found for an id that is not a UUID", async () => {
    const requests = stubFetch(() => Response.json({}))
    await expect(loadItem("not-a-uuid")).rejects.toBeInstanceOf(NotFound)
    expect(requests).toHaveLength(0)
  })

  test("rethrows any other failure", async () => {
    stubFetch(() => Response.json({ detail: "boom" }, { status: 500 }))
    const error = await loadItem(ITEM_ID).catch((e: unknown) => e)
    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ status: 500 })
  })
})

describe("getUser", () => {
  test("is null without a session, and asks nothing of the API", async () => {
    session.token = undefined
    const requests = stubFetch(() => Response.json(USER))
    expect(await getUser()).toBeNull()
    expect(requests).toHaveLength(0)
  })

  test("returns the signed-in user", async () => {
    stubFetch(() => Response.json(USER))
    expect(await getUser()).toEqual(USER)
  })

  test("is null when the token is rejected", async () => {
    stubFetch(() => Response.json({ detail: "x" }, { status: 401 }))
    expect(await getUser()).toBeNull()
  })
})
