import { type NextRequest, NextResponse } from "next/server"
import { SESSION_COOKIE } from "@/lib/config"

const publicRoutes = [
  "/login",
  "/signup",
  "/recover-password",
  "/reset-password",
]

// Guards the routes that require a session.
export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl
  const isPublic = publicRoutes.includes(pathname)
  const hasSession = request.cookies.has(SESSION_COOKIE)

  if (!isPublic && !hasSession) {
    return NextResponse.redirect(new URL("/login", request.nextUrl))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|assets|favicon.ico).*)"],
}
