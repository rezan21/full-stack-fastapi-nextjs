import type { Metadata } from "next"
import { redirect } from "next/navigation"
import { ResetPasswordForm } from "@/components/auth/ResetPasswordForm"

export const metadata: Metadata = { title: "Reset Password - FastAPI Template" }

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ token?: string }>
}) {
  const { token } = await searchParams
  if (!token) redirect("/login")

  return <ResetPasswordForm token={token} />
}
