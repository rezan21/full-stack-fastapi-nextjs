"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useForm } from "react-hook-form"
import type { z } from "zod"
import { completeSignup, resetPassword } from "@/actions/auth"
import { zNewPassword } from "@/client/zod.gen"
import { FormField } from "@/components/common/FormField"
import { PasswordInput } from "@/components/common/PasswordInput"
import { Button } from "@/components/ui/button"
import { FieldGroup } from "@/components/ui/field"
import { Spinner } from "@/components/ui/spinner"
import { useCustomToast } from "@/hooks/use-custom-toast"
import { formError } from "@/lib/form-errors"
import { withPasswordConfirmation } from "@/lib/schemas"

const formSchema = withPasswordConfirmation(
  zNewPassword.pick({ new_password: true }),
  "new_password",
)

type FormData = z.infer<typeof formSchema>

const VARIANTS = {
  reset: {
    title: "Reset Password",
    submit: "Reset Password",
    success: "Password updated successfully",
    action: resetPassword,
  },
  signup: {
    title: "Set your password",
    submit: "Create Account",
    success: "Account created successfully",
    action: completeSignup,
  },
}

// Form that sets a password from an emailed link.
export function SetPasswordForm({
  token,
  variant,
}: {
  token: string
  variant: keyof typeof VARIANTS
}) {
  const { title, submit, success, action } = VARIANTS[variant]
  const router = useRouter()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema, { error: formError }),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: { new_password: "", confirm_password: "" },
  })

  const onSubmit = async (data: FormData) => {
    const res = await action(token, data.new_password)
    if (res.error) {
      showErrorToast(res.error)
      return
    }
    showSuccessToast(success)
    form.reset()
    router.push("/login")
  }

  return (
    <form
      onSubmit={form.handleSubmit(onSubmit)}
      className="flex flex-col gap-6"
    >
      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
      </div>

      <FieldGroup>
        <FormField
          control={form.control}
          name="new_password"
          label="New Password"
        >
          {(field) => (
            <PasswordInput
              {...field}
              data-testid="new-password-input"
              placeholder="New Password"
            />
          )}
        </FormField>

        <FormField
          control={form.control}
          name="confirm_password"
          label="Confirm Password"
        >
          {(field) => (
            <PasswordInput
              {...field}
              data-testid="confirm-password-input"
              placeholder="Confirm Password"
            />
          )}
        </FormField>

        <Button
          type="submit"
          className="w-full"
          disabled={form.formState.isSubmitting}
        >
          {form.formState.isSubmitting && <Spinner data-icon="inline-start" />}
          {submit}
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
