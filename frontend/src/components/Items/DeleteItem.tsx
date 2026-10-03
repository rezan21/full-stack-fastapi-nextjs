"use client"

import { Trash2 } from "lucide-react"
import { useRouter } from "next/navigation"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { deleteItem } from "@/actions/items"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { DropdownMenuItem } from "@/components/ui/dropdown-menu"
import { Spinner } from "@/components/ui/spinner"
import useCustomToast from "@/hooks/useCustomToast"

export function DeleteItem({
  id,
  onSuccess,
  redirectTo,
}: {
  id: string
  onSuccess: () => void
  redirectTo?: string
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
    if (redirectTo) router.replace(redirectTo)
    else router.refresh()
  }

  return (
    <AlertDialog open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuItem
        variant="destructive"
        closeOnClick={false}
        onClick={() => setIsOpen(true)}
      >
        <Trash2 />
        Delete Item
      </DropdownMenuItem>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Item</AlertDialogTitle>
          <AlertDialogDescription>
            This item will be permanently deleted. Are you sure? You will not be
            able to undo this action.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={formState.isSubmitting}>
            Cancel
          </AlertDialogCancel>
          <AlertDialogAction
            variant="destructive"
            disabled={formState.isSubmitting}
            onClick={handleSubmit(onSubmit)}
          >
            {formState.isSubmitting && <Spinner data-icon="inline-start" />}
            Delete
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
