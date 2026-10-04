import type { Metadata } from "next"
import { CheckEmail } from "@/components/auth/CheckEmail"

export const metadata: Metadata = {
  title: "Check Your Email - FastAPI Template",
}

// Confirmation shown after a password recovery request.
export default function Page() {
  return (
    <CheckEmail>
      If an account exists for that email, we've sent a link to reset your
      password.
    </CheckEmail>
  )
}
