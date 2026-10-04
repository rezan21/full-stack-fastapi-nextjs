import { beforeEach, describe, expect, test } from "bun:test"
import { API_URL, SESSION_COOKIE } from "@/lib/config"
import {
  cookieWrites,
  Redirect,
  resetServer,
  revalidated,
  session,
  stubFetch,
} from "@/test-support"

const {
  completeSignup,
  confirmEmailChange,
  login,
  logout,
  recoverPassword,
  resetPassword,
  signup,
} = await import("@/actions/auth")

const failure = () =>
  Response.json({ detail: "Nope, not that." }, { status: 400 })

beforeEach(resetServer)

describe("login", () => {
  test("starts a session from the access token", async () => {
    const requests = stubFetch(() =>
      Response.json({
        access_token: "fresh-token",
        token_type: "bearer",
        expires_in: 600,
      }),
    )
    expect(await login("user@example.com", "password123")).toEqual({})
    expect(requests[0].url).toBe(`${API_URL}/api/v1/login/access-token`)
    expect(cookieWrites).toMatchObject([
      { name: SESSION_COOKIE, value: "fresh-token", options: { maxAge: 600 } },
    ])
  })

  test("returns the error and starts no session when the login fails", async () => {
    stubFetch(failure)
    session.token = undefined
    expect(await login("user@example.com", "wrong-password")).toEqual({
      error: "Nope, not that.",
    })
    expect(cookieWrites).toHaveLength(0)
  })
})

describe("logout", () => {
  test("retires the tokens, ends the session and goes to the login page", async () => {
    const requests = stubFetch(() => new Response(null, { status: 204 }))
    await expect(logout()).rejects.toEqual(new Redirect("/login"))
    expect(requests[0]).toMatchObject({
      method: "POST",
      url: `${API_URL}/api/v1/logout`,
    })
    expect(session.token).toBeUndefined()
  })

  test("still ends the session when the backend cannot be reached", async () => {
    stubFetch(() => {
      throw new TypeError("network down")
    })
    await expect(logout()).rejects.toEqual(new Redirect("/login"))
    expect(session.token).toBeUndefined()
  })
})

describe("signup", () => {
  const data = { email: "new@example.com", full_name: "New User" }

  test("requests the sign-up link", async () => {
    const requests = stubFetch(() => Response.json({ message: "sent" }))
    expect(await signup(data)).toEqual({})
    expect(requests[0]).toMatchObject({ method: "POST" })
    expect(requests[0].url).toBe(`${API_URL}/api/v1/users/signup`)
    expect(JSON.parse(requests[0].body)).toEqual(data)
  })

  test("returns the error when the request fails", async () => {
    stubFetch(failure)
    expect(await signup(data)).toEqual({ error: "Nope, not that." })
  })
})

describe("completeSignup", () => {
  test("creates the user with the token and the chosen password", async () => {
    const requests = stubFetch(() => Response.json({}, { status: 201 }))
    expect(await completeSignup("a-token", "password123")).toEqual({})
    expect(requests[0].url).toBe(`${API_URL}/api/v1/users/signup/complete`)
    expect(JSON.parse(requests[0].body)).toEqual({
      token: "a-token",
      new_password: "password123",
    })
  })

  test("returns the error when the token is rejected", async () => {
    stubFetch(failure)
    expect(await completeSignup("a-token", "password123")).toEqual({
      error: "Nope, not that.",
    })
  })
})

describe("confirmEmailChange", () => {
  test("applies the change and refreshes the layout so the new email shows", async () => {
    const requests = stubFetch(() => Response.json({ message: "done" }))
    expect(await confirmEmailChange("a-token")).toEqual({})
    expect(requests[0].url).toBe(`${API_URL}/api/v1/users/confirm-email`)
    expect(JSON.parse(requests[0].body)).toEqual({ token: "a-token" })
    expect(revalidated).toEqual([["/", "layout"]])
  })

  test("returns the error and refreshes nothing when the token is rejected", async () => {
    stubFetch(failure)
    expect(await confirmEmailChange("a-token")).toEqual({
      error: "Nope, not that.",
    })
    expect(revalidated).toHaveLength(0)
  })
})

describe("recoverPassword", () => {
  test("requests a recovery email", async () => {
    const requests = stubFetch(() => Response.json({ message: "sent" }))
    expect(await recoverPassword({ email: "user@example.com" })).toEqual({})
    expect(requests[0].url).toBe(`${API_URL}/api/v1/password-recovery`)
  })

  test("returns the error when the request fails", async () => {
    stubFetch(failure)
    expect(await recoverPassword({ email: "user@example.com" })).toEqual({
      error: "Nope, not that.",
    })
  })
})

describe("resetPassword", () => {
  test("sets the new password with the token", async () => {
    const requests = stubFetch(() => Response.json({ message: "done" }))
    expect(await resetPassword("a-token", "password123")).toEqual({})
    expect(JSON.parse(requests[0].body)).toEqual({
      token: "a-token",
      new_password: "password123",
    })
  })

  test("returns the error when the token is rejected", async () => {
    stubFetch(failure)
    expect(await resetPassword("a-token", "password123")).toEqual({
      error: "Nope, not that.",
    })
  })
})
