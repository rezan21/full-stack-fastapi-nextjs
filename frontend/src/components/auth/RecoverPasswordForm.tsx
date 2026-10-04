"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useForm } from "react-hook-form"
import type { z } from "zod"
import { recoverPassword } from "@/actions/auth"
import { zPasswordRecovery } from "@/client/zod.gen"
import { FormField } from "@/components/common/FormField"
import { Button } from "@/components/ui/button"
import { FieldGroup } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import { useCustomToast } from "@/hooks/use-custom-toast"
import { formError } from "@/lib/form-errors"

type FormData = z.infer<typeof zPasswordRecovery>

// Password recovery form.
export function RecoverPasswordForm() {
  const router = useRouter()
  const { showErrorToast } = useCustomToast()
  const form = useForm<FormData>({
    resolver: zodResolver(zPasswordRecovery, { error: formError }),
    defaultValues: { email: "" },
  })

  const onSubmit = async (data: FormData) => {
    const res = await recoverPassword(data)
    if (res.error) {
      showErrorToast(res.error)
      return
    }
    router.replace("/recover-password/sent")
  }

  return (
    <form
      onSubmit={form.handleSubmit(onSubmit)}
      className="flex flex-col gap-6"
    >
      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-2xl font-bold tracking-tight">Password Recovery</h1>
      </div>

      <FieldGroup>
        <FormField control={form.control} name="email" label="Email">
          {(field) => (
            <Input
              {...field}
              data-testid="email-input"
              placeholder="user@example.com"
              type="email"
            />
          )}
        </FormField>

        <Button
          type="submit"
          className="w-full"
          disabled={form.formState.isSubmitting}
        >
          {form.formState.isSubmitting && <Spinner data-icon="inline-start" />}
          Continue
        </Button>
      </FieldGroup>

      <div className="text-center text-sm">
        Remember your password?{" "}
        <Link href="/login" className="underline underline-offset-4">
          Log in
        </Link>
      </div>
    </form>
  )
}
