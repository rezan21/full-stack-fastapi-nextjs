import { type NextRequest, NextResponse } from "next/server"
import { SESSION_COOKIE } from "@/lib/config"

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

// Builds the Content-Security-Policy that allows only scripts carrying the nonce.
function contentSecurityPolicy(nonce: string) {
  const dev = process.env.NODE_ENV === "development"
  return [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${dev ? " 'unsafe-eval'" : ""}`,
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' blob: data:",
    "font-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
  ].join("; ")
}

// Guards the routes that require a session and sets the Content-Security-Policy.
export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl
  const isPublic = publicRoutes.includes(pathname)
  const hasSession = request.cookies.has(SESSION_COOKIE)

  if (!isPublic && !hasSession) {
    return NextResponse.redirect(new URL("/login", request.nextUrl))
  }

  const nonce = btoa(crypto.randomUUID())
  const policy = contentSecurityPolicy(nonce)
  const headers = new Headers(request.headers)
  headers.set("x-nonce", nonce)
  headers.set("Content-Security-Policy", policy)
  const response = NextResponse.next({ request: { headers } })
  response.headers.set("Content-Security-Policy", policy)
  return response
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|assets|favicon.ico).*)"],
}
