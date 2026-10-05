import { type NextRequest, NextResponse } from "next/server"
import { SESSION_COOKIE } from "@/lib/config"
import { contentSecurityPolicy } from "@/lib/csp"

const publicRoutes = [
  "/login",
  "/signup",
  "/signup/sent",
  "/signup/complete",
  "/confirm-email",
  "/recover-password",
  "/recover-password/sent",
  "/reset-password",
]

// Guards the routes that require a session and sets the Content-Security-Policy.
export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl
  const isPublic = publicRoutes.includes(pathname)
  const hasSession = request.cookies.has(SESSION_COOKIE)

  if (!isPublic && !hasSession) {
    return NextResponse.redirect(new URL("/login", request.nextUrl))
  }

  const nonce = btoa(crypto.randomUUID())
  const policy = contentSecurityPolicy(
    `'self' 'nonce-${nonce}' 'strict-dynamic'`,
  )
  const headers = new Headers(request.headers)
  headers.set("x-nonce", nonce)
  headers.set("Content-Security-Policy", policy)
  const response = NextResponse.next({ request: { headers } })
  response.headers.set("Content-Security-Policy", policy)
  return response
}

export const config = {
  matcher: ["/((?!api|chat/run$|_next/static|_next/image|favicon.ico).+)"],
}
