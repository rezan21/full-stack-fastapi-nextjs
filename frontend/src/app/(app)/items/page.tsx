import { Search } from "lucide-react"
import type { Metadata } from "next"
import { AddItem } from "@/components/Items/AddItem"
import { ItemsTable } from "@/components/Items/ItemsTable"
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
        <div className="flex flex-col items-center justify-center text-center py-12">
          <div className="rounded-full bg-muted p-4 mb-4">
            <Search className="h-8 w-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold">
            You don't have any items yet
          </h3>
          <p className="text-muted-foreground">Add a new item to get started</p>
        </div>
      ) : (
        <ItemsTable items={items.data} />
      )}
    </div>
  )
}
