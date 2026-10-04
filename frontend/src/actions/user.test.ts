import { beforeEach, describe, expect, test } from "bun:test"
import { API_URL, SESSION_COOKIE } from "@/lib/config"
import {
  cookieWrites,
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

const emailChange = {
  email: "new@example.com",
  current_password: "old-password",
}

const passwordChange = {
  current_password: "old-password",
  new_password: "new-password",
}

const renewedToken = () =>
  Response.json({
    access_token: "renewed-token",
    token_type: "bearer",
    expires_in: 600,
  })

beforeEach(resetServer)

const cases = [
  ["updateProfile", () => updateProfile({ full_name: "New Name" })],
  ["changeEmail", () => changeEmail(emailChange)],
  ["changePassword", () => changePassword(passwordChange)],
  ["deleteAccount", () => deleteAccount({ current_password: "old-password" })],
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
    expect(await changeEmail(emailChange)).toEqual({})
    expect(requests[0].url).toBe(`${API_URL}/api/v1/users/me/email`)
    expect(JSON.parse(requests[0].body)).toEqual(emailChange)
  })

  test("does not refresh the layout, since nothing changes yet", async () => {
    stubFetch(() => Response.json({ message: "sent" }))
    await changeEmail(emailChange)
    expect(revalidated).toHaveLength(0)
  })
})

describe("changePassword", () => {
  test("changes the password", async () => {
    const requests = stubFetch(renewedToken)
    expect(await changePassword(passwordChange)).toEqual({})
    expect(requests[0]).toMatchObject({ method: "PATCH" })
  })

  test("keeps this device signed in with the renewed token", async () => {
    stubFetch(renewedToken)
    await changePassword(passwordChange)
    expect(cookieWrites).toMatchObject([
      {
        name: SESSION_COOKIE,
        value: "renewed-token",
        options: { maxAge: 600 },
      },
    ])
  })

  test("leaves the session alone when the change fails", async () => {
    stubFetch(failure)
    await changePassword(passwordChange)
    expect(cookieWrites).toHaveLength(0)
    expect(session.token).toBe("test-token")
  })
})

describe("deleteAccount", () => {
  test("ends the session and goes to the login page", async () => {
    stubFetch(() => new Response(null, { status: 204 }))
    await expect(
      deleteAccount({ current_password: "old-password" }),
    ).rejects.toEqual(new Redirect("/login"))
    expect(session.token).toBeUndefined()
  })

  test("sends the current password", async () => {
    const requests = stubFetch(() => new Response(null, { status: 204 }))
    await deleteAccount({ current_password: "old-password" }).catch(() => {})
    expect(requests[0]).toMatchObject({ method: "DELETE" })
    expect(JSON.parse(requests[0].body)).toEqual({
      current_password: "old-password",
    })
  })

  test("keeps the session when the password is wrong", async () => {
    stubFetch(failure)
    expect(await deleteAccount({ current_password: "wrong" })).toEqual({
      error: "Not allowed.",
    })
    expect(session.token).toBe("test-token")
  })
})
