"use client"

import {
  createColumnHelper,
  tableFeatures,
  useTable,
} from "@tanstack/react-table"
import { Check, Copy } from "lucide-react"
import Link from "next/link"
import type { ReactNode } from "react"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useCopyToClipboard } from "@/hooks/useCopyToClipboard"
import type { ItemPublic } from "@/lib/api"
import { cn } from "@/lib/utils"
import { ItemActionsMenu } from "./ItemActionsMenu"
import { ITEM_COLUMNS, type ItemColumnId } from "./item-columns"

// Copyable item id.
function CopyId({ id }: { id: string }) {
  const [copiedText, copy] = useCopyToClipboard()
  const isCopied = copiedText === id

  return (
    <div className="flex items-center gap-1.5 group">
      <span className="font-mono text-xs text-muted-foreground">{id}</span>
      <Button
        variant="ghost"
        size="icon-xs"
        className="opacity-0 group-hover:opacity-100 transition-opacity"
        onClick={() => copy(id)}
      >
        {isCopied ? <Check className="text-primary" /> : <Copy />}
        <span className="sr-only">Copy ID</span>
      </Button>
    </div>
  )
}

const features = tableFeatures({})
const columnHelper = createColumnHelper<typeof features, ItemPublic>()

const renderCell: Record<ItemColumnId, (item: ItemPublic) => ReactNode> = {
  id: (item) => <CopyId id={item.id} />,
  title: (item) => (
    <Link href={`/items/${item.id}`} className="font-medium hover:underline">
      {item.title}
    </Link>
  ),
  description: (item) => (
    <span
      className={cn(
        "max-w-xs truncate block text-muted-foreground",
        !item.description && "italic",
      )}
    >
      {item.description || "No description"}
    </span>
  ),
  actions: (item) => (
    <div className="flex justify-end">
      <ItemActionsMenu item={item} />
    </div>
  ),
}

const columns = columnHelper.columns(
  ITEM_COLUMNS.map((column) =>
    columnHelper.display({
      id: column.id,
      header: column.srOnlyHeader
        ? () => <span className="sr-only">{column.header}</span>
        : column.header,
      cell: ({ row }) => renderCell[column.id](row.original),
    }),
  ),
)

// Table of items.
export function ItemsTable({ items }: { items: ItemPublic[] }) {
  const table = useTable({
    features,
    columns,
    data: items,
    getRowId: (item) => item.id,
  })

  return (
    <div className="flex flex-col gap-4">
      <Table>
        <TableHeader>
          {table.getHeaderGroups().map((headerGroup) => (
            <TableRow key={headerGroup.id} className="hover:bg-transparent">
              {headerGroup.headers.map((header) => (
                <TableHead key={header.id}>
                  {header.isPlaceholder ? null : (
                    <table.FlexRender header={header} />
                  )}
                </TableHead>
              ))}
            </TableRow>
          ))}
        </TableHeader>
        <TableBody>
          {table.getRowModel().rows.map((row) => (
            <TableRow key={row.id}>
              {row.getAllCells().map((cell) => (
                <TableCell key={cell.id}>
                  <table.FlexRender cell={cell} />
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
