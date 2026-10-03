"use client"

import { EllipsisVertical } from "lucide-react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import type { ItemPublic } from "@/lib/api"
import { DeleteItem } from "./DeleteItem"
import { EditItem } from "./EditItem"

export function ItemActionsMenu({
  item,
  redirectTo,
}: {
  item: ItemPublic
  redirectTo?: string
}) {
  const [open, setOpen] = useState(false)

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger render={<Button variant="ghost" size="icon" />}>
        <EllipsisVertical />
        <span className="sr-only">Item actions</span>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuGroup>
          <EditItem item={item} onSuccess={() => setOpen(false)} />
          <DeleteItem
            id={item.id}
            onSuccess={() => setOpen(false)}
            redirectTo={redirectTo}
          />
        </DropdownMenuGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
