"use client"

import { useRouter } from "next/navigation"
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
import { Spinner } from "@/components/ui/spinner"
import useCustomToast from "@/hooks/useCustomToast"

// Dialog for deleting an item.
export function DeleteItem({
  id,
  open,
  onOpenChange,
  redirectTo,
}: {
  id: string
  open: boolean
  onOpenChange: (open: boolean) => void
  redirectTo?: string
}) {
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
    onOpenChange(false)
    if (redirectTo) router.replace(redirectTo)
    else router.refresh()
  }

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
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
