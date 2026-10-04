"use client"

import { useRouter } from "next/navigation"
import { useTransition } from "react"
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
import { useCustomToast } from "@/hooks/use-custom-toast"

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
  const [isPending, startTransition] = useTransition()

  const onConfirm = () =>
    startTransition(async () => {
      const res = await deleteItem(id)
      if (res.error) {
        showErrorToast(res.error)
        return
      }
      showSuccessToast("The item was deleted successfully")
      onOpenChange(false)
      if (redirectTo) router.replace(redirectTo)
    })

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
          <AlertDialogCancel disabled={isPending}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            variant="destructive"
            disabled={isPending}
            onClick={onConfirm}
          >
            {isPending && <Spinner data-icon="inline-start" />}
            Delete
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
