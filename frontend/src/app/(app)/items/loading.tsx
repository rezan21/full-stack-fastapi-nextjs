import { PageHeader } from "@/components/Common/PageHeader"
import PendingItems from "@/components/Pending/PendingItems"

// Loading state for the items page.
export default function Loading() {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Items" description="Create and manage your items" />
      <PendingItems />
    </div>
  )
}
