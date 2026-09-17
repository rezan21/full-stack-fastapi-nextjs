"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import Link from "next/link"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { recoverPassword } from "@/actions/auth"
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

const formSchema = z.object({
  email: z.email({ message: "Invalid email address" }),
})

type FormData = z.infer<typeof formSchema>

export function RecoverPasswordForm() {
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: { email: "" },
  })

  const onSubmit = async (data: FormData) => {
    const res = await recoverPassword(data.email)
    if (res.error) {
      showErrorToast(res.error)
      return
    }
    showSuccessToast("Password recovery email sent successfully")
    form.reset()
  }

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit(onSubmit)}
        className="flex flex-col gap-6"
      >
        <div className="flex flex-col items-center gap-2 text-center">
          <h1 className="text-2xl font-bold">Password Recovery</h1>
        </div>

        <div className="grid gap-4">
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email</FormLabel>
                <FormControl>
                  <Input
                    data-testid="email-input"
                    placeholder="user@example.com"
                    type="email"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <LoadingButton
            type="submit"
            className="w-full"
            loading={form.formState.isSubmitting}
          >
            Continue
          </LoadingButton>
        </div>

        <div className="text-center text-sm">
          Remember your password?{" "}
          <Link href="/login" className="underline underline-offset-4">
            Log in
          </Link>
        </div>
      </form>
    </Form>
  )
}
