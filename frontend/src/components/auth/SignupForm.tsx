"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useForm } from "react-hook-form"
import type { z } from "zod"
import { signup } from "@/actions/auth"
import { zUserRegister } from "@/client/zod.gen"
import { FormField } from "@/components/common/FormField"
import { Button } from "@/components/ui/button"
import { FieldGroup } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import { useCustomToast } from "@/hooks/use-custom-toast"
import { formError } from "@/lib/form-errors"

type FormData = z.infer<typeof zUserRegister>

// Sign-up form.
export function SignupForm() {
  const router = useRouter()
  const { showErrorToast } = useCustomToast()
  const form = useForm<FormData>({
    resolver: zodResolver(zUserRegister, { error: formError }),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: { email: "", full_name: "" },
  })

  const onSubmit = async (data: FormData) => {
    const res = await signup(data)
    if (res.error) {
      showErrorToast(res.error)
      return
    }
    router.replace("/signup/sent")
  }

  return (
    <form
      onSubmit={form.handleSubmit(onSubmit)}
      className="flex flex-col gap-6"
    >
      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-2xl font-bold tracking-tight">Create an account</h1>
      </div>

      <FieldGroup>
        <FormField control={form.control} name="full_name" label="Full Name">
          {(field) => (
            <Input
              {...field}
              data-testid="full-name-input"
              placeholder="User"
              type="text"
            />
          )}
        </FormField>

        <FormField control={form.control} name="email" label="Email">
          {(field) => (
            <Input
              {...field}
              data-testid="email-input"
              placeholder="user@example.com"
              type="email"
            />
          )}
        </FormField>

        <Button
          type="submit"
          className="w-full"
          disabled={form.formState.isSubmitting}
        >
          {form.formState.isSubmitting && <Spinner data-icon="inline-start" />}
          Sign Up
        </Button>
      </FieldGroup>

      <div className="text-center text-sm">
        Already have an account?{" "}
        <Link href="/login" className="underline underline-offset-4">
          Log in
        </Link>
      </div>
    </form>
  )
}
