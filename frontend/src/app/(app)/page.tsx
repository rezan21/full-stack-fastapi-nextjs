import type { Metadata } from "next"
import { PageHeader } from "@/components/Common/PageHeader"
import { getUser } from "@/lib/dal"

export const metadata: Metadata = { title: "Dashboard - FastAPI Template" }

export default async function Page() {
  const user = await getUser()

  return (
    <PageHeader
      title={`Hi, ${user?.full_name || user?.email} 👋`}
      description="Welcome back, nice to see you again!"
    />
  )
}
