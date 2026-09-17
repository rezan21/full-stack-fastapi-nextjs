"use client"

import { Pencil } from "lucide-react"
import { updateItem } from "@/actions/items"
import { DropdownMenuItem } from "@/components/ui/dropdown-menu"
import type { ItemPublic } from "@/lib/api"
import { ItemFormDialog } from "./ItemFormDialog"

export function EditItem({
  item,
  onSuccess,
}: {
  item: ItemPublic
  onSuccess: () => void
}) {
  return (
    <ItemFormDialog
      title="Edit Item"
      description="Update the item details below."
      defaultValues={{
        title: item.title,
        description: item.description ?? undefined,
      }}
      action={(data) => updateItem(item.id, data)}
      successMessage="Item updated successfully"
      onDone={onSuccess}
      trigger={(open) => (
        <DropdownMenuItem onSelect={(e) => e.preventDefault()} onClick={open}>
          <Pencil />
          Edit Item
        </DropdownMenuItem>
      )}
    />
  )
}
