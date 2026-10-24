import { Search } from "lucide-react"
import type { Metadata } from "next"
import { redirect } from "next/navigation"
import { PageHeader } from "@/components/common/PageHeader"
import { PagePagination } from "@/components/common/PagePagination"
import { AddItem } from "@/components/items/AddItem"
import { ItemsTable } from "@/components/items/ItemsTable"
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty"
import { getItems } from "@/lib/api"
import { ITEMS_PAGE_SIZE } from "@/lib/config"
import { pageCount, pageHref, parsePage } from "@/lib/pagination"

export const metadata: Metadata = { title: "Items - FastAPI Template" }

// Items list page.
export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ page?: string | string[] }>
}) {
  const page = parsePage((await searchParams).page)
  const items = await getItems(page)
  const pages = pageCount(items.count, ITEMS_PAGE_SIZE)
  if (page > pages) redirect(pageHref("/items", pages))

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Items" description="Create and manage your items">
        <AddItem />
      </PageHeader>

      {items.count === 0 ? (
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
        <>
          <ItemsTable items={items.data} />
          <PagePagination basePath="/items" page={page} pages={pages} />
        </>
      )}
    </div>
  )
}
