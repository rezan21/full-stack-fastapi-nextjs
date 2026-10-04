import { redirect } from "next/navigation"
import type { ReactNode } from "react"
import { AuthLayout } from "@/components/common/AuthLayout"
import { getUser } from "@/lib/dal"

// Layout for the authentication pages.
export default async function Layout({ children }: { children: ReactNode }) {
  const user = await getUser()
  if (user) redirect("/dashboard")

  return <AuthLayout>{children}</AuthLayout>
}
