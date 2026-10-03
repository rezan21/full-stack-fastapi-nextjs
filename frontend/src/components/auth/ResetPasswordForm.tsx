"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Controller, useForm } from "react-hook-form"
import type { z } from "zod"
import { resetPassword } from "@/actions/auth"
import { zNewPassword } from "@/client/zod.gen"
import { PasswordInput } from "@/components/Common/PasswordInput"
import { Button } from "@/components/ui/button"
import {
  Field,
  FieldError,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field"
import { Spinner } from "@/components/ui/spinner"
import useCustomToast from "@/hooks/useCustomToast"
import { formError } from "@/lib/form-errors"
import { withPasswordConfirmation } from "@/lib/schemas"

const formSchema = withPasswordConfirmation(
  zNewPassword.pick({ new_password: true }),
  "new_password",
)

type FormData = z.infer<typeof formSchema>

export function ResetPasswordForm({ token }: { token: string }) {
  const router = useRouter()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema, { error: formError }),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: { new_password: "", confirm_password: "" },
  })

  const onSubmit = async (data: FormData) => {
    const res = await resetPassword(token, data.new_password)
    if (res.error) {
      showErrorToast(res.error)
      return
    }
    showSuccessToast("Password updated successfully")
    form.reset()
    router.push("/login")
  }

  return (
    <form
      onSubmit={form.handleSubmit(onSubmit)}
      className="flex flex-col gap-6"
    >
      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-2xl font-bold tracking-tight">Reset Password</h1>
      </div>

      <FieldGroup>
        <Controller
          control={form.control}
          name="new_password"
          render={({ field, fieldState }) => (
            <Field data-invalid={fieldState.invalid}>
              <FieldLabel htmlFor={field.name}>New Password</FieldLabel>
              <PasswordInput
                {...field}
                id={field.name}
                data-testid="new-password-input"
                placeholder="New Password"
                aria-invalid={fieldState.invalid}
              />
              {fieldState.error && <FieldError errors={[fieldState.error]} />}
            </Field>
          )}
        />

        <Controller
          control={form.control}
          name="confirm_password"
          render={({ field, fieldState }) => (
            <Field data-invalid={fieldState.invalid}>
              <FieldLabel htmlFor={field.name}>Confirm Password</FieldLabel>
              <PasswordInput
                {...field}
                id={field.name}
                data-testid="confirm-password-input"
                placeholder="Confirm Password"
                aria-invalid={fieldState.invalid}
              />
              {fieldState.error && <FieldError errors={[fieldState.error]} />}
            </Field>
          )}
        />

        <Button
          type="submit"
          className="w-full"
          disabled={form.formState.isSubmitting}
        >
          {form.formState.isSubmitting && <Spinner data-icon="inline-start" />}
          Reset Password
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
