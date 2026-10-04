"use client"

import { useState, useTransition } from "react"
import { deleteAccount } from "@/actions/user"
import { PasswordInput } from "@/components/Common/PasswordInput"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"
import { Field, FieldLabel } from "@/components/ui/field"
import { Spinner } from "@/components/ui/spinner"
import useCustomToast from "@/hooks/useCustomToast"

// Account deletion control.
export function DeleteAccount() {
  const [isOpen, setIsOpen] = useState(false)
  const [password, setPassword] = useState("")
  const [isPending, startTransition] = useTransition()
  const { showErrorToast } = useCustomToast()

  const onConfirm = () =>
    startTransition(async () => {
      const res = await deleteAccount({ current_password: password })
      if (res.error) showErrorToast(res.error)
    })

  const onOpenChange = (open: boolean) => {
    setIsOpen(open)
    if (!open) setPassword("")
  }

  return (
    <AlertDialog open={isOpen} onOpenChange={onOpenChange}>
      <AlertDialogTrigger render={<Button variant="destructive" />}>
        Delete Account
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Account</AlertDialogTitle>
          <AlertDialogDescription>
            Your account and all your items will be permanently deleted. You
            will not be able to undo this action.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <Field>
          <FieldLabel htmlFor="delete-account-password">
            Confirm with your password
          </FieldLabel>
          <PasswordInput
            id="delete-account-password"
            data-testid="delete-account-password-input"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </Field>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isPending}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            variant="destructive"
            disabled={isPending || password === ""}
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
