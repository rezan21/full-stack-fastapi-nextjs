import "server-only"
import { cookies } from "next/headers"
import { SESSION_COOKIE } from "@/lib/config"

// Returns the session token, if any.
export async function getToken(): Promise<string | undefined> {
  return (await cookies()).get(SESSION_COOKIE)?.value
}

// Starts a session from an access token.
export async function createSession(
  token: string,
  maxAge: number,
): Promise<void> {
  const cookieStore = await cookies()
  cookieStore.set(SESSION_COOKIE, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge,
    path: "/",
  })
}

// Ends the session.
export async function deleteSession(): Promise<void> {
  const cookieStore = await cookies()
  cookieStore.delete(SESSION_COOKIE)
}
