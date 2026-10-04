import { beforeEach, describe, expect, test } from "bun:test"
import { API_URL } from "@/lib/config"
import {
  ITEM,
  resetServer,
  revalidated,
  session,
  stubFetch,
} from "@/test-support"

const { createItem, deleteItem, updateItem } = await import("@/actions/items")

const failure = () => Response.json({ detail: "Not yours." }, { status: 403 })

beforeEach(resetServer)

const cases = [
  ["createItem", () => createItem({ title: "A title" })],
  ["updateItem", () => updateItem(ITEM.id, { title: "A title" })],
  ["deleteItem", () => deleteItem(ITEM.id)],
] as const

for (const [name, run] of cases) {
  describe(name, () => {
    test("asks nothing of the API without a session", async () => {
      session.token = undefined
      const requests = stubFetch(() => Response.json(ITEM))
      expect(await run()).toEqual({ error: "Not authenticated" })
      expect(requests).toHaveLength(0)
    })

    test("returns the API error and leaves the list alone", async () => {
      stubFetch(failure)
      expect(await run()).toEqual({ error: "Not yours." })
      expect(revalidated).toHaveLength(0)
    })

    test("refreshes the items list after it succeeds", async () => {
      stubFetch(() => new Response(JSON.stringify(ITEM), { status: 200 }))
      expect(await run()).toEqual({})
      expect(revalidated).toEqual([["/items", undefined]])
    })
  })
}

describe("requests", () => {
  test("createItem posts the item", async () => {
    const requests = stubFetch(() => Response.json(ITEM, { status: 201 }))
    await createItem({ title: "A title", description: "Details" })
    expect(requests[0]).toMatchObject({
      method: "POST",
      url: `${API_URL}/api/v1/items`,
    })
    expect(JSON.parse(requests[0].body)).toEqual({
      title: "A title",
      description: "Details",
    })
  })

  test("updateItem patches the item", async () => {
    const requests = stubFetch(() => Response.json(ITEM))
    await updateItem(ITEM.id, { title: "New" })
    expect(requests[0]).toMatchObject({
      method: "PATCH",
      url: `${API_URL}/api/v1/items/${ITEM.id}`,
    })
  })

  test("deleteItem deletes the item", async () => {
    const requests = stubFetch(() => new Response(null, { status: 204 }))
    await deleteItem(ITEM.id)
    expect(requests[0]).toMatchObject({
      method: "DELETE",
      url: `${API_URL}/api/v1/items/${ITEM.id}`,
    })
  })

  test("a network failure becomes a generic error", async () => {
    stubFetch(() => {
      throw new TypeError("network down")
    })
    expect(await createItem({ title: "A title" })).toEqual({
      error: "Something went wrong.",
    })
  })
})
