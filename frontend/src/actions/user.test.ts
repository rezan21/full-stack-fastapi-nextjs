import { beforeEach, describe, expect, test } from "bun:test"
import { API_URL } from "@/lib/config"
import {
  Redirect,
  resetServer,
  revalidated,
  session,
  stubFetch,
  USER,
} from "@/test-support"

const { changeEmail, changePassword, deleteAccount, updateProfile } =
  await import("@/actions/user")

const failure = () => Response.json({ detail: "Not allowed." }, { status: 400 })

beforeEach(resetServer)

const cases = [
  ["updateProfile", () => updateProfile({ full_name: "New Name" })],
  ["changeEmail", () => changeEmail({ email: "new@example.com" })],
  [
    "changePassword",
    () =>
      changePassword({
        current_password: "old-password",
        new_password: "new-password",
      }),
  ],
  ["deleteAccount", () => deleteAccount()],
] as const

for (const [name, run] of cases) {
  describe(name, () => {
    test("asks nothing of the API without a session", async () => {
      session.token = undefined
      const requests = stubFetch(() => Response.json(USER))
      expect(await run()).toEqual({ error: "Not authenticated" })
      expect(requests).toHaveLength(0)
    })

    test("returns the API error", async () => {
      stubFetch(failure)
      expect(await run()).toEqual({ error: "Not allowed." })
    })
  })
}

describe("updateProfile", () => {
  test("refreshes the layout so the new name shows", async () => {
    stubFetch(() => Response.json(USER))
    expect(await updateProfile({ full_name: "New Name" })).toEqual({})
    expect(revalidated).toEqual([["/", "layout"]])
  })
})

describe("changeEmail", () => {
  test("requests the link that confirms the new address", async () => {
    const requests = stubFetch(() => Response.json({ message: "sent" }))
    expect(await changeEmail({ email: "new@example.com" })).toEqual({})
    expect(requests[0].url).toBe(`${API_URL}/api/v1/users/me/email`)
    expect(JSON.parse(requests[0].body)).toEqual({ email: "new@example.com" })
  })

  test("does not refresh the layout, since nothing changes yet", async () => {
    stubFetch(() => Response.json({ message: "sent" }))
    await changeEmail({ email: "new@example.com" })
    expect(revalidated).toHaveLength(0)
  })
})

describe("changePassword", () => {
  test("changes the password", async () => {
    const requests = stubFetch(() => Response.json({ message: "done" }))
    expect(
      await changePassword({
        current_password: "old-password",
        new_password: "new-password",
      }),
    ).toEqual({})
    expect(requests[0]).toMatchObject({ method: "PATCH" })
  })
})

describe("deleteAccount", () => {
  test("ends the session and goes to the login page", async () => {
    stubFetch(() => new Response(null, { status: 204 }))
    await expect(deleteAccount()).rejects.toEqual(new Redirect("/login"))
    expect(session.token).toBeUndefined()
  })
})
