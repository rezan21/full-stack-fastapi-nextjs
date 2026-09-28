import { Search } from "lucide-react"
import type { Metadata } from "next"
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Items</h1>
          <p className="text-muted-foreground">Create and manage your items</p>
        </div>
        <AddItem />
      </div>

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
