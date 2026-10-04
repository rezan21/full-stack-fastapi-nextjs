import type { Metadata } from "next"
import { CheckEmail } from "@/components/auth/CheckEmail"

export const metadata: Metadata = {
  title: "Check Your Email - FastAPI Template",
}

// Confirmation shown after a sign-up request.
export default function Page() {
  return (
    <CheckEmail>
      If that email can be used to sign up, we've sent a link to finish creating
      your account.
    </CheckEmail>
  )
}
