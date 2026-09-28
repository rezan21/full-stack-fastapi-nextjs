import type { Metadata } from "next"
import { getUser } from "@/lib/dal"

export const metadata: Metadata = { title: "Dashboard - FastAPI Template" }

export default async function Page() {
  const user = await getUser()

  return (
    <div>
      <h1 className="text-2xl font-bold tracking-tight truncate max-w-sm">
        Hi, {user?.full_name || user?.email} 👋
      </h1>
      <p className="text-muted-foreground">
        Welcome back, nice to see you again!
      </p>
    </div>
  )
}
