import { describe, expect, test } from "bun:test"
import { API_URL } from "@/lib/config"
import { ITEM, stubFetch } from "@/test-support"

const {
  ApiError,
  changePassword,
  createItem,
  deleteAccount,
  deleteItem,
  getCurrentUser,
  getItem,
  getItems,
  loginAccessToken,
  recoverPassword,
  registerUser,
  resetPassword,
  updateItem,
  updateProfile,
} = await import("@/lib/api")

const ITEM_ID = ITEM.id

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
    await getItems()
    expect(requests[0].authorization).toBe("Bearer test-token")
  })

  test("list items with the backend's paging defaults", async () => {
    const requests = stubFetch(() => Response.json({ data: [], count: 0 }))
    await getItems()
    expect(requests).toHaveLength(1)
    expect(requests[0].method).toBe("GET")
    expect(requests[0].url).toBe(`${API_URL}/api/v1/items/`)
  })

  test("post a typed body as JSON", async () => {
    const requests = stubFetch(() => Response.json({ id: ITEM_ID }))
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
    expect(requests[0].url).toBe(`${API_URL}/api/v1/password-recovery/`)
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
    ["deleteAccount", () => deleteAccount(), "DELETE", "/users/me"],
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
      () =>
        registerUser({
          email: "user@example.com",
          password: "password123",
          full_name: "A User",
        }),
      "POST",
      "/users/signup",
    ],
    [
      "resetPassword",
      () => resetPassword("a-token", "password123"),
      "POST",
      "/reset-password/",
    ],
    [
      "updateItem",
      () => updateItem(ITEM_ID, { title: "New title" }),
      "PUT",
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
    expect(await failureOf(getItems())).toMatchObject({
      message: "upstream down",
      status: 502,
    })
  })

  test("fall back to the status text, then to a generic message", async () => {
    stubFetch(
      () =>
        new Response("", { status: 500, statusText: "Internal Server Error" }),
    )
    expect(await failureOf(getItems())).toMatchObject({
      message: "Internal Server Error",
    })
    stubFetch(() => new Response("", { status: 500 }))
    expect(await failureOf(getItems())).toMatchObject({
      message: "Something went wrong.",
    })
  })

  test("pass a network error through unchanged", async () => {
    stubFetch(() => {
      throw new TypeError("fetch failed")
    })
    const error = await failureOf(getItems())
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
