"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { ItemFields } from "@/components/items/ItemFields"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { FieldGroup } from "@/components/ui/field"
import { Spinner } from "@/components/ui/spinner"
import { formError } from "@/lib/form-errors"
import { type ItemFormData, itemFormSchema } from "@/lib/schemas"

// Form in the chat for the details of an item the assistant needs from the user.
export function ItemForm({
  heading,
  defaultValues,
  onSubmit,
  onCancel,
}: {
  heading: string
  defaultValues: ItemFormData
  onSubmit: (data: ItemFormData) => Promise<void>
  onCancel: () => void
}) {
  const [error, setError] = useState<string>()
  const form = useForm<ItemFormData>({
    resolver: zodResolver(itemFormSchema, { error: formError }),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues,
  })

  const submit = async (data: ItemFormData) => {
    setError(undefined)
    try {
      await onSubmit(data)
    } catch {
      setError("The item could not be saved. Try again.")
    }
  }

  return (
    <Card size="sm">
      <CardHeader>
        <CardTitle>{heading}</CardTitle>
        <CardDescription>Fill in the details of the item.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={form.handleSubmit(submit)}>
          <FieldGroup>
            <ItemFields control={form.control} />
          </FieldGroup>

          <div className="mt-4 flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              disabled={form.formState.isSubmitting}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={form.formState.isSubmitting}>
              {form.formState.isSubmitting && (
                <Spinner data-icon="inline-start" />
              )}
              Save
            </Button>
          </div>
          {error && (
            <p role="alert" className="mt-2 text-sm text-destructive">
              {error}
            </p>
          )}
        </form>
      </CardContent>
    </Card>
  )
}
