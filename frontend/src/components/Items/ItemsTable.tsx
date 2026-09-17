"use client"

import { Check, Copy } from "lucide-react"
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

function CopyId({ id }: { id: string }) {
  const [copiedText, copy] = useCopyToClipboard()
  const isCopied = copiedText === id

  return (
    <div className="flex items-center gap-1.5 group">
      <span className="font-mono text-xs text-muted-foreground">{id}</span>
      <Button
        variant="ghost"
        size="icon"
        className="size-6 opacity-0 group-hover:opacity-100 transition-opacity"
        onClick={() => copy(id)}
      >
        {isCopied ? (
          <Check className="size-3 text-primary" />
        ) : (
          <Copy className="size-3" />
        )}
        <span className="sr-only">Copy ID</span>
      </Button>
    </div>
  )
}

export function ItemsTable({ items }: { items: ItemPublic[] }) {
  return (
    <div className="flex flex-col gap-4">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead>ID</TableHead>
            <TableHead>Title</TableHead>
            <TableHead>Description</TableHead>
            <TableHead>
              <span className="sr-only">Actions</span>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {items.map((item) => (
            <TableRow key={item.id}>
              <TableCell>
                <CopyId id={item.id} />
              </TableCell>
              <TableCell>
                <span className="font-medium">{item.title}</span>
              </TableCell>
              <TableCell>
                <span
                  className={cn(
                    "max-w-xs truncate block text-muted-foreground",
                    !item.description && "italic",
                  )}
                >
                  {item.description || "No description"}
                </span>
              </TableCell>
              <TableCell>
                <div className="flex justify-end">
                  <ItemActionsMenu item={item} />
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
