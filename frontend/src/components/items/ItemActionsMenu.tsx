"use client"

import { EllipsisVertical, Pencil, Trash2 } from "lucide-react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import type { ItemPublic } from "@/lib/api"
import { DeleteItem } from "./DeleteItem"
import { EditItem } from "./EditItem"

type ItemDialog = "edit" | "delete" | null

// Actions menu for an item.
export function ItemActionsMenu({
  item,
  redirectTo,
}: {
  item: ItemPublic
  redirectTo?: string
}) {
  const [dialog, setDialog] = useState<ItemDialog>(null)

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger render={<Button variant="ghost" size="icon" />}>
          <EllipsisVertical />
          <span className="sr-only">Item actions</span>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuGroup>
            <DropdownMenuItem onClick={() => setDialog("edit")}>
              <Pencil />
              Edit Item
            </DropdownMenuItem>
            <DropdownMenuItem
              variant="destructive"
              onClick={() => setDialog("delete")}
            >
              <Trash2 />
              Delete Item
            </DropdownMenuItem>
          </DropdownMenuGroup>
        </DropdownMenuContent>
      </DropdownMenu>

      <EditItem
        item={item}
        open={dialog === "edit"}
        onOpenChange={(open) => setDialog(open ? "edit" : null)}
      />
      <DeleteItem
        id={item.id}
        open={dialog === "delete"}
        onOpenChange={(open) => setDialog(open ? "delete" : null)}
        redirectTo={redirectTo}
      />
    </>
  )
}
