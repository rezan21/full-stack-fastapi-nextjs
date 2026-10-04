import type { Metadata } from "next"
import { redirect } from "next/navigation"
import { ConfirmEmailForm } from "@/components/auth/ConfirmEmailForm"
import { AuthLayout } from "@/components/Common/AuthLayout"

export const metadata: Metadata = { title: "Confirm Email - FastAPI Template" }

// Email change confirmation page.
export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ token?: string }>
}) {
  const { token } = await searchParams
  if (!token) redirect("/login")

  return (
    <AuthLayout>
      <ConfirmEmailForm token={token} />
    </AuthLayout>
  )
}
