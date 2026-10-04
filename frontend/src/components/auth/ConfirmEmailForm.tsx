"use client"

import { useRouter } from "next/navigation"
import { useState } from "react"
import { confirmEmailChange } from "@/actions/auth"
import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import useCustomToast from "@/hooks/useCustomToast"

// Email change confirmation form.
export function ConfirmEmailForm({ token }: { token: string }) {
  const router = useRouter()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const confirm = async () => {
    setIsSubmitting(true)
    const res = await confirmEmailChange(token)
    if (res.error) {
      setIsSubmitting(false)
      showErrorToast(res.error)
      return
    }
    showSuccessToast("Email updated successfully")
    router.replace("/settings")
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-2xl font-bold tracking-tight">
          Confirm your new email
        </h1>
        <p className="text-sm text-muted-foreground">
          Confirm that you want to use this address for your account.
        </p>
      </div>

      <Button className="w-full" disabled={isSubmitting} onClick={confirm}>
        {isSubmitting && <Spinner data-icon="inline-start" />}
        Confirm email
      </Button>
    </div>
  )
}
