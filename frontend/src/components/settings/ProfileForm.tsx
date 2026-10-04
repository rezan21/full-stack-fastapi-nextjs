"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { changeEmail, updateProfile } from "@/actions/user"
import { zEmailChange, zUserUpdateMe } from "@/client/zod.gen"
import { FormField } from "@/components/common/FormField"
import { PasswordInput } from "@/components/common/PasswordInput"
import { Button } from "@/components/ui/button"
import { Field, FieldGroup, FieldTitle } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import { useCustomToast } from "@/hooks/use-custom-toast"
import type { UserPublic } from "@/lib/api"
import { formError } from "@/lib/form-errors"

// Builds the profile schema, which asks for the password only when the email changes.
function profileSchema(currentEmail: string) {
  return zUserUpdateMe
    .required({ full_name: true })
    .extend({
      email: zEmailChange.shape.email,
      current_password: zEmailChange.shape.current_password.or(z.literal("")),
    })
    .refine(
      (data) => data.email === currentEmail || data.current_password !== "",
      {
        error: "Current password is required to change the email",
        path: ["current_password"],
      },
    )
}

type FormData = z.infer<ReturnType<typeof profileSchema>>

// Maps a user to the profile form values.
function toFormData(user: UserPublic): FormData {
  return { full_name: user.full_name, email: user.email, current_password: "" }
}

// Read-only field.
function ReadOnlyField({ title, value }: { title: string; value: string }) {
  return (
    <Field>
      <FieldTitle>{title}</FieldTitle>
      <p className="text-sm text-muted-foreground">{value}</p>
    </Field>
  )
}

// Profile form.
export function ProfileForm({ user }: { user: UserPublic }) {
  const [isEditing, setIsEditing] = useState(false)
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const form = useForm<FormData>({
    resolver: zodResolver(profileSchema(user.email), { error: formError }),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: toFormData(user),
  })

  const startEditing = () => {
    form.reset(toFormData(user))
    setIsEditing(true)
  }

  const onSubmit = async (data: FormData) => {
    const emailChanged = data.email !== user.email
    if (emailChanged) {
      const emailRes = await changeEmail({
        email: data.email,
        current_password: data.current_password,
      })
      if (emailRes.error) {
        showErrorToast(emailRes.error)
        return
      }
    }
    const res = await updateProfile({ full_name: data.full_name })
    if (res.error) {
      showErrorToast(res.error)
      return
    }
    showSuccessToast(
      emailChanged
        ? "Check your new email to confirm the change"
        : "User updated successfully",
    )
    setIsEditing(false)
  }

  return (
    <form
      onSubmit={form.handleSubmit(onSubmit)}
      className="flex flex-col gap-6"
    >
      <FieldGroup>
        {isEditing ? (
          <FormField control={form.control} name="full_name" label="Full name">
            {(field) => (
              <Input {...field} placeholder="Full name" type="text" />
            )}
          </FormField>
        ) : (
          <ReadOnlyField title="Full name" value={user.full_name} />
        )}

        {isEditing ? (
          <FormField
            control={form.control}
            name="email"
            label="Email"
            description="A new address only takes effect once you confirm it from the link we send there."
          >
            {(field) => (
              <Input {...field} placeholder="user@example.com" type="email" />
            )}
          </FormField>
        ) : (
          <ReadOnlyField title="Email" value={user.email} />
        )}

        {isEditing && form.watch("email") !== user.email && (
          <FormField
            control={form.control}
            name="current_password"
            label="Current password"
          >
            {(field) => (
              <PasswordInput
                {...field}
                data-testid="current-password-input"
                placeholder="Current password"
                autoComplete="current-password"
              />
            )}
          </FormField>
        )}
      </FieldGroup>

      <div className="flex gap-2">
        {isEditing ? (
          <>
            <Button
              key="save"
              type="submit"
              disabled={form.formState.isSubmitting}
            >
              {form.formState.isSubmitting && (
                <Spinner data-icon="inline-start" />
              )}
              Save
            </Button>
            <Button
              key="cancel"
              type="button"
              variant="outline"
              disabled={form.formState.isSubmitting}
              onClick={() => setIsEditing(false)}
            >
              Cancel
            </Button>
          </>
        ) : (
          <Button key="edit" type="button" onClick={startEditing}>
            Edit
          </Button>
        )}
      </div>
    </form>
  )
}
