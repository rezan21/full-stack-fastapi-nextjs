"use client"

import { Check, Copy } from "lucide-react"
import Link from "next/link"
import type { ReactNode } from "react"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableRow } from "@/components/ui/table"
import { useCopyToClipboard } from "@/hooks/use-copy-to-clipboard"
import type { ItemPublic } from "@/lib/api"
import { cn } from "@/lib/utils"
import { ItemActionsMenu } from "./ItemActionsMenu"
import { ItemsTableHeader } from "./ItemsTableHeader"
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

// Table of items.
export function ItemsTable({ items }: { items: ItemPublic[] }) {
  return (
    <Table>
      <ItemsTableHeader />
      <TableBody>
        {items.map((item) => (
          <TableRow key={item.id}>
            {ITEM_COLUMNS.map((column) => (
              <TableCell key={column.id}>
                {renderCell[column.id](item)}
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
