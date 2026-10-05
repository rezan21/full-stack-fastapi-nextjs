import { PageHeader } from "@/components/common/PageHeader"
import { Skeleton } from "@/components/ui/skeleton"

// Loading state for the AI chat pages.
export default function Loading() {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="AI Chat" description="Talk to the assistant" />
      <Skeleton className="h-64 w-full" />
    </div>
  )
}
