import type { Metadata } from "next"
import { RecoverPasswordForm } from "@/components/auth/RecoverPasswordForm"

export const metadata: Metadata = {
  title: "Recover Password - FastAPI Template",
}

export default function Page() {
  return <RecoverPasswordForm />
}
