import type { Metadata } from "next"
import { LoginForm } from "@/components/auth/LoginForm"

export const metadata: Metadata = { title: "Log In - FastAPI Template" }

export default function Page() {
  return <LoginForm />
}
