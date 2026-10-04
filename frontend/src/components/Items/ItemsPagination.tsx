import { ChevronLeft, ChevronRight } from "lucide-react"
import Link from "next/link"
import type { ReactNode } from "react"
import { Button } from "@/components/ui/button"
import {
  Pagination,
  PaginationContent,
  PaginationItem,
} from "@/components/ui/pagination"
import { itemsPageHref } from "@/lib/pagination"

function PageLink({
  page,
  label,
  children,
}: {
  page: number | null
  label: string
  children: ReactNode
}) {
  if (page === null) {
    return (
      <Button variant="ghost" aria-label={label} disabled>
        {children}
      </Button>
    )
  }
  return (
    <Button
      variant="ghost"
      nativeButton={false}
      render={<Link href={itemsPageHref(page)} aria-label={label} />}
    >
      {children}
    </Button>
  )
}

export function ItemsPagination({
  page,
  pages,
}: {
  page: number
  pages: number
}) {
  if (pages <= 1) return null

  return (
    <Pagination>
      <PaginationContent>
        <PaginationItem>
          <PageLink
            page={page > 1 ? page - 1 : null}
            label="Go to previous page"
          >
            <ChevronLeft data-icon="inline-start" />
            Previous
          </PageLink>
        </PaginationItem>
        <PaginationItem>
          <span className="px-3 text-sm text-muted-foreground">
            Page {page} of {pages}
          </span>
        </PaginationItem>
        <PaginationItem>
          <PageLink
            page={page < pages ? page + 1 : null}
            label="Go to next page"
          >
            Next
            <ChevronRight data-icon="inline-end" />
          </PageLink>
        </PaginationItem>
      </PaginationContent>
    </Pagination>
  )
}
