"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { useState } from "react"
import { Controller, useForm } from "react-hook-form"
import type { z } from "zod"
import { changeEmail, updateProfile } from "@/actions/user"
import { zEmailChange, zUserUpdateMe } from "@/client/zod.gen"
import { Button } from "@/components/ui/button"
import {
  Field,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
  FieldTitle,
} from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import useCustomToast from "@/hooks/useCustomToast"
import type { UserPublic } from "@/lib/api"
import { formError } from "@/lib/form-errors"

const formSchema = zUserUpdateMe
  .required({ full_name: true })
  .extend({ email: zEmailChange.shape.email })

type FormData = z.infer<typeof formSchema>

// Maps a user to the profile form values.
function toFormData(user: UserPublic): FormData {
  return { full_name: user.full_name, email: user.email }
}

// Profile form.
export function ProfileForm({ user }: { user: UserPublic }) {
  const [isEditing, setIsEditing] = useState(false)
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema, { error: formError }),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: toFormData(user),
  })

  const startEditing = () => {
    form.reset(toFormData(user))
    setIsEditing(true)
  }

  const onSubmit = async (data: FormData) => {
    const res = await updateProfile({ full_name: data.full_name })
    if (res.error) {
      showErrorToast(res.error)
      return
    }
    if (data.email !== user.email) {
      const emailRes = await changeEmail({ email: data.email })
      if (emailRes.error) {
        showErrorToast(emailRes.error)
        return
      }
      showSuccessToast("Check your new email to confirm the change")
    } else {
      showSuccessToast("User updated successfully")
    }
    setIsEditing(false)
  }

  return (
    <form
      onSubmit={form.handleSubmit(onSubmit)}
      className="flex flex-col gap-6"
    >
      <FieldGroup>
        <Controller
          control={form.control}
          name="full_name"
          render={({ field, fieldState }) => (
            <Field data-invalid={fieldState.invalid}>
              {isEditing ? (
                <>
                  <FieldLabel htmlFor={field.name}>Full name</FieldLabel>
                  <Input
                    {...field}
                    id={field.name}
                    placeholder="Full name"
                    type="text"
                    aria-invalid={fieldState.invalid}
                  />
                  {fieldState.error && (
                    <FieldError errors={[fieldState.error]} />
                  )}
                </>
              ) : (
                <>
                  <FieldTitle>Full name</FieldTitle>
                  <p className="text-sm text-muted-foreground">
                    {user.full_name}
                  </p>
                </>
              )}
            </Field>
          )}
        />

        <Controller
          control={form.control}
          name="email"
          render={({ field, fieldState }) => (
            <Field data-invalid={fieldState.invalid}>
              {isEditing ? (
                <>
                  <FieldLabel htmlFor={field.name}>Email</FieldLabel>
                  <Input
                    {...field}
                    id={field.name}
                    placeholder="user@example.com"
                    type="email"
                    aria-invalid={fieldState.invalid}
                  />
                  <FieldDescription>
                    A new address only takes effect once you confirm it from the
                    link we send there.
                  </FieldDescription>
                  {fieldState.error && (
                    <FieldError errors={[fieldState.error]} />
                  )}
                </>
              ) : (
                <>
                  <FieldTitle>Email</FieldTitle>
                  <p className="text-sm text-muted-foreground">{user.email}</p>
                </>
              )}
            </Field>
          )}
        />
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
