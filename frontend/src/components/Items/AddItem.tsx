"use client"

import { Plus } from "lucide-react"
import { useState } from "react"
import { createItem } from "@/actions/items"
import { Button } from "@/components/ui/button"
import { ItemFormDialog } from "./ItemFormDialog"

export function AddItem() {
  const [open, setOpen] = useState(false)

  return (
    <>
      <Button onClick={() => setOpen(true)}>
        <Plus data-icon="inline-start" />
        Add Item
      </Button>
      <ItemFormDialog
        title="Add Item"
        description="Fill in the details to add a new item."
        defaultValues={{ title: "", description: "" }}
        action={createItem}
        successMessage="Item created successfully"
        open={open}
        onOpenChange={setOpen}
      />
    </>
  )
}
