import { PageHeader } from "@/components/common/PageHeader"
import { PendingItems } from "@/components/pending/PendingItems"

// Loading state for the items page.
export default function Loading() {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Items" description="Create and manage your items" />
      <PendingItems />
    </div>
  )
}
