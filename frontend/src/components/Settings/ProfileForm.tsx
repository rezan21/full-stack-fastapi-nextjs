"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { useState } from "react"
import { Controller, useForm } from "react-hook-form"
import type { z } from "zod"
import { updateProfile } from "@/actions/user"
import { zUserUpdateMe } from "@/client/zod.gen"
import { Button } from "@/components/ui/button"
import {
  Field,
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

const formSchema = zUserUpdateMe.extend({
  full_name: zUserUpdateMe.shape.full_name.unwrap().unwrap().min(1),
  email: zUserUpdateMe.shape.email.unwrap().unwrap(),
})

type FormData = z.infer<typeof formSchema>

function toFormData(user: UserPublic): FormData {
  return { full_name: user.full_name ?? "", email: user.email }
}

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
    const res = await updateProfile(data)
    if (res.error) {
      showErrorToast(res.error)
      return
    }
    showSuccessToast("User updated successfully")
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
                    {user.full_name || "Not set"}
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
