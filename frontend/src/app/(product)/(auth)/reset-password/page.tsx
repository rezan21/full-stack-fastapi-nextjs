import type { Metadata } from "next"
import { redirect } from "next/navigation"
import { SetPasswordForm } from "@/components/auth/SetPasswordForm"

export const metadata: Metadata = { title: "Reset Password - FastAPI Template" }

// Reset password page.
export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ token?: string }>
}) {
  const { token } = await searchParams
  if (!token) redirect("/login")

  return <SetPasswordForm token={token} variant="reset" />
}
