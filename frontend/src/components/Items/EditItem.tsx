"use client"

import { updateItem } from "@/actions/items"
import type { ItemPublic } from "@/lib/api"
import { ItemFormDialog } from "./ItemFormDialog"

export function EditItem({
  item,
  open,
  onOpenChange,
}: {
  item: ItemPublic
  open: boolean
  onOpenChange: (open: boolean) => void
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
      open={open}
      onOpenChange={onOpenChange}
    />
  )
}
