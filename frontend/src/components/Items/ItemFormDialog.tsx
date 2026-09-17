"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { useRouter } from "next/navigation"
import { type ReactNode, useState } from "react"
import { useForm } from "react-hook-form"
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
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import useCustomToast from "@/hooks/useCustomToast"
import { type ItemFormData, itemFormSchema } from "@/lib/schemas"

export function ItemFormDialog({
  trigger,
  title,
  description,
  defaultValues,
  action,
  successMessage,
  onDone,
}: {
  trigger: (open: () => void) => ReactNode
  title: string
  description: string
  defaultValues: ItemFormData
  action: (data: ItemFormData) => Promise<{ error?: string }>
  successMessage: string
  onDone?: () => void
}) {
  const [isOpen, setIsOpen] = useState(false)
  const router = useRouter()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const form = useForm<ItemFormData>({
    resolver: zodResolver(itemFormSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues,
  })

  const onSubmit = async (data: ItemFormData) => {
    const res = await action(data)
    if (res.error) {
      showErrorToast(res.error)
      return
    }
    showSuccessToast(successMessage)
    form.reset()
    setIsOpen(false)
    onDone?.()
    router.refresh()
  }

  return (
    <>
      {trigger(() => setIsOpen(true))}
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="sm:max-w-md">
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)}>
              <DialogHeader>
                <DialogTitle>{title}</DialogTitle>
                <DialogDescription>{description}</DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <FormField
                  control={form.control}
                  name="title"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>
                        Title <span className="text-destructive">*</span>
                      </FormLabel>
                      <FormControl>
                        <Input placeholder="Title" type="text" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="description"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Description</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="Description"
                          type="text"
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <DialogFooter>
                <DialogClose asChild>
                  <Button
                    variant="outline"
                    disabled={form.formState.isSubmitting}
                  >
                    Cancel
                  </Button>
                </DialogClose>
                <LoadingButton
                  type="submit"
                  loading={form.formState.isSubmitting}
                >
                  Save
                </LoadingButton>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>
    </>
  )
}
