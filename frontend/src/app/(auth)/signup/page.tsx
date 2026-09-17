import type { Metadata } from "next"
import { SignupForm } from "@/components/auth/SignupForm"

export const metadata: Metadata = { title: "Sign Up - FastAPI Template" }

export default function Page() {
  return <SignupForm />
}
