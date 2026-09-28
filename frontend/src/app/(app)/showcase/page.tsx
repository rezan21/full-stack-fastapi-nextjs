import type { Metadata } from "next"
import { PageHeader } from "@/components/Common/PageHeader"
import { Showcase } from "@/components/Showcase/Showcase"

export const metadata: Metadata = { title: "Showcase - FastAPI Template" }

export default function Page() {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Showcase"
        description="A reference of the UI components and theme tokens available in this template"
      />
      <Showcase />
    </div>
  )
}
