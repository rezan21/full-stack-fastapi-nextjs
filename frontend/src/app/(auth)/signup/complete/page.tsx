import type { Metadata } from "next"
import { redirect } from "next/navigation"
import { SetPasswordForm } from "@/components/auth/SetPasswordForm"

export const metadata: Metadata = { title: "Set Password - FastAPI Template" }

// Sign-up completion page.
export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ token?: string }>
}) {
  const { token } = await searchParams
  if (!token) redirect("/login")

  return <SetPasswordForm token={token} variant="signup" />
}
