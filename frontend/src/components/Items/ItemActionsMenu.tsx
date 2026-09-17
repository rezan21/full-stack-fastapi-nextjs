"use client"

import { EllipsisVertical } from "lucide-react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import type { ItemPublic } from "@/lib/api"
import { DeleteItem } from "./DeleteItem"
import { EditItem } from "./EditItem"

export function ItemActionsMenu({ item }: { item: ItemPublic }) {
  const [open, setOpen] = useState(false)

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon">
          <EllipsisVertical />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <EditItem item={item} onSuccess={() => setOpen(false)} />
        <DeleteItem id={item.id} onSuccess={() => setOpen(false)} />
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
