"use client"

import { Trash2 } from "lucide-react"
import { useRouter } from "next/navigation"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { deleteItem } from "@/actions/items"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { DropdownMenuItem } from "@/components/ui/dropdown-menu"
import { Spinner } from "@/components/ui/spinner"
import useCustomToast from "@/hooks/useCustomToast"

export function DeleteItem({
  id,
  onSuccess,
}: {
  id: string
  onSuccess: () => void
}) {
  const [isOpen, setIsOpen] = useState(false)
  const router = useRouter()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const { handleSubmit, formState } = useForm()

  const onSubmit = async () => {
    const res = await deleteItem(id)
    if (res.error) {
      showErrorToast(res.error)
      return
    }
    showSuccessToast("The item was deleted successfully")
    setIsOpen(false)
    onSuccess()
    router.refresh()
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuItem
        variant="destructive"
        closeOnClick={false}
        onClick={() => setIsOpen(true)}
      >
        <Trash2 />
        Delete Item
      </DropdownMenuItem>
      <DialogContent className="sm:max-w-md">
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Delete Item</DialogTitle>
            <DialogDescription>
              This item will be permanently deleted. Are you sure? You will not
              be able to undo this action.
            </DialogDescription>
          </DialogHeader>

          <DialogFooter className="mt-4">
            <DialogClose
              render={
                <Button variant="outline" disabled={formState.isSubmitting} />
              }
            >
              Cancel
            </DialogClose>
            <Button
              variant="destructive"
              type="submit"
              disabled={formState.isSubmitting}
            >
              {formState.isSubmitting && <Spinner data-icon="inline-start" />}
              Delete
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
