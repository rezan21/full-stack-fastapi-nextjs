"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import type { z } from "zod"
import { changePassword } from "@/actions/user"
import { zUpdatePassword } from "@/client/zod.gen"
import { FormField } from "@/components/common/FormField"
import { PasswordInput } from "@/components/common/PasswordInput"
import { Button } from "@/components/ui/button"
import { FieldGroup } from "@/components/ui/field"
import { Spinner } from "@/components/ui/spinner"
import { useCustomToast } from "@/hooks/use-custom-toast"
import { formError } from "@/lib/form-errors"
import { withPasswordConfirmation } from "@/lib/schemas"

const formSchema = withPasswordConfirmation(zUpdatePassword, "new_password")

type FormData = z.infer<typeof formSchema>

// Change password form.
export function PasswordForm() {
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema, { error: formError }),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      current_password: "",
      new_password: "",
      confirm_password: "",
    },
  })

  const onSubmit = async (data: FormData) => {
    const res = await changePassword({
      current_password: data.current_password,
      new_password: data.new_password,
    })
    if (res.error) {
      showErrorToast(res.error)
      return
    }
    showSuccessToast("Password updated successfully")
    form.reset()
  }

  return (
    <form
      onSubmit={form.handleSubmit(onSubmit)}
      className="flex flex-col gap-6"
    >
      <FieldGroup>
        <FormField
          control={form.control}
          name="current_password"
          label="Current Password"
        >
          {(field) => (
            <PasswordInput
              {...field}
              data-testid="current-password-input"
              placeholder="Current Password"
            />
          )}
        </FormField>

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
      </FieldGroup>

      <Button
        type="submit"
        className="self-start"
        disabled={form.formState.isSubmitting}
      >
        {form.formState.isSubmitting && <Spinner data-icon="inline-start" />}
        Update Password
      </Button>
    </form>
  )
}
