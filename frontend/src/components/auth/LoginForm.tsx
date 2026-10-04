"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useForm } from "react-hook-form"
import type { z } from "zod"
import { login } from "@/actions/auth"
import { zCredentials } from "@/client/zod.gen"
import { FormField } from "@/components/common/FormField"
import { PasswordInput } from "@/components/common/PasswordInput"
import { Button } from "@/components/ui/button"
import { FieldGroup } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import { useCustomToast } from "@/hooks/use-custom-toast"
import { formError } from "@/lib/form-errors"

type FormData = z.infer<typeof zCredentials>

// Login form.
export function LoginForm() {
  const router = useRouter()
  const { showErrorToast } = useCustomToast()
  const form = useForm<FormData>({
    resolver: zodResolver(zCredentials, { error: formError }),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: { username: "", password: "" },
  })

  const onSubmit = async (data: FormData) => {
    const res = await login(data.username, data.password)
    if (res.error) {
      showErrorToast(res.error)
      return
    }
    router.push("/")
    router.refresh()
  }

  return (
    <form
      onSubmit={form.handleSubmit(onSubmit)}
      className="flex flex-col gap-6"
    >
      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-2xl font-bold tracking-tight">
          Login to your account
        </h1>
      </div>

      <FieldGroup>
        <FormField control={form.control} name="username" label="Email">
          {(field) => (
            <Input
              {...field}
              data-testid="email-input"
              placeholder="user@example.com"
              type="email"
            />
          )}
        </FormField>

        <FormField
          control={form.control}
          name="password"
          label="Password"
          labelAside={
            <Link
              href="/recover-password"
              className="ml-auto text-sm underline-offset-4 hover:underline"
            >
              Forgot your password?
            </Link>
          }
        >
          {(field) => (
            <PasswordInput
              {...field}
              data-testid="password-input"
              placeholder="Password"
            />
          )}
        </FormField>

        <Button type="submit" disabled={form.formState.isSubmitting}>
          {form.formState.isSubmitting && <Spinner data-icon="inline-start" />}
          Log In
        </Button>
      </FieldGroup>

      <div className="text-center text-sm">
        Don't have an account yet?{" "}
        <Link href="/signup" className="underline underline-offset-4">
          Sign up
        </Link>
      </div>
    </form>
  )
}
