import { beforeEach, describe, expect, test } from "bun:test"
import { SESSION_COOKIE } from "@/lib/config"
import { cookieWrites, resetServer, session } from "@/test-support"

const { createSession, deleteSession, getToken } = await import("@/lib/session")

beforeEach(resetServer)

describe("getToken", () => {
  test("returns the token in the session cookie", async () => {
    expect(await getToken()).toBe("test-token")
  })

  test("is undefined without a session", async () => {
    session.token = undefined
    expect(await getToken()).toBeUndefined()
  })
})

describe("createSession", () => {
  test("stores the token in a cookie that scripts cannot read", async () => {
    await createSession("a-token", 3600)
    expect(cookieWrites).toEqual([
      {
        name: SESSION_COOKIE,
        value: "a-token",
        options: {
          httpOnly: true,
          secure: false,
          sameSite: "lax",
          maxAge: 3600,
          path: "/",
        },
      },
    ])
  })

  test("marks the cookie secure in production", async () => {
    const before = process.env.NODE_ENV
    Object.assign(process.env, { NODE_ENV: "production" })
    try {
      await createSession("a-token", 3600)
    } finally {
      Object.assign(process.env, { NODE_ENV: before })
    }
    expect(cookieWrites[0].options).toMatchObject({ secure: true })
  })
})

describe("deleteSession", () => {
  test("clears the session cookie", async () => {
    await deleteSession()
    expect(await getToken()).toBeUndefined()
  })
})
