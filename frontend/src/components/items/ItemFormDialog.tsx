"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { FormField } from "@/components/common/FormField"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { FieldGroup } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import { useCustomToast } from "@/hooks/use-custom-toast"
import { formError } from "@/lib/form-errors"
import { type ItemFormData, itemFormSchema } from "@/lib/schemas"

// Dialog form for an item.
export function ItemFormDialog({
  title,
  description,
  defaultValues,
  action,
  successMessage,
  open,
  onOpenChange,
}: {
  title: string
  description: string
  defaultValues: ItemFormData
  action: (data: ItemFormData) => Promise<{ error?: string }>
  successMessage: string
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const form = useForm<ItemFormData>({
    resolver: zodResolver(itemFormSchema, { error: formError }),
    mode: "onBlur",
    criteriaMode: "all",
    values: defaultValues,
  })

  const handleOpenChange = (isOpen: boolean) => {
    if (!isOpen) form.reset()
    onOpenChange(isOpen)
  }

  const onSubmit = async (data: ItemFormData) => {
    const res = await action(data)
    if (res.error) {
      showErrorToast(res.error)
      return
    }
    showSuccessToast(successMessage)
    handleOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>{title}</DialogTitle>
            <DialogDescription>{description}</DialogDescription>
          </DialogHeader>
          <FieldGroup className="py-4">
            <FormField
              control={form.control}
              name="title"
              label={
                <>
                  Title <span className="text-destructive">*</span>
                </>
              }
            >
              {(field) => <Input {...field} placeholder="Title" type="text" />}
            </FormField>

            <FormField
              control={form.control}
              name="description"
              label="Description"
            >
              {(field) => (
                <Input
                  {...field}
                  value={field.value ?? ""}
                  placeholder="Description"
                  type="text"
                />
              )}
            </FormField>
          </FieldGroup>

          <DialogFooter>
            <DialogClose
              render={
                <Button
                  variant="outline"
                  disabled={form.formState.isSubmitting}
                />
              }
            >
              Cancel
            </DialogClose>
            <Button type="submit" disabled={form.formState.isSubmitting}>
              {form.formState.isSubmitting && (
                <Spinner data-icon="inline-start" />
              )}
              Save
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
