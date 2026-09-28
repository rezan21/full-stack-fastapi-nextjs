import { Search } from "lucide-react"
import type { Metadata } from "next"
import { PageHeader } from "@/components/Common/PageHeader"
import { AddItem } from "@/components/Items/AddItem"
import { ItemsTable } from "@/components/Items/ItemsTable"
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty"
import { getItems } from "@/lib/api"

export const metadata: Metadata = { title: "Items - FastAPI Template" }

export default async function Page() {
  const items = await getItems()

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Items" description="Create and manage your items">
        <AddItem />
      </PageHeader>

      {items.data.length === 0 ? (
        <Empty>
          <EmptyHeader>
            <EmptyMedia variant="icon">
              <Search />
            </EmptyMedia>
            <EmptyTitle>You don't have any items yet</EmptyTitle>
            <EmptyDescription>Add a new item to get started</EmptyDescription>
          </EmptyHeader>
        </Empty>
      ) : (
        <ItemsTable items={items.data} />
      )}
    </div>
  )
}
