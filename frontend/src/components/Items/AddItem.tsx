"use client"

import { Plus } from "lucide-react"
import { createItem } from "@/actions/items"
import { Button } from "@/components/ui/button"
import { ItemFormDialog } from "./ItemFormDialog"

export function AddItem() {
  return (
    <ItemFormDialog
      title="Add Item"
      description="Fill in the details to add a new item."
      defaultValues={{ title: "", description: "" }}
      action={createItem}
      successMessage="Item created successfully"
      trigger={(open) => (
        <Button className="my-4" onClick={open}>
          <Plus />
          Add Item
        </Button>
      )}
    />
  )
}
