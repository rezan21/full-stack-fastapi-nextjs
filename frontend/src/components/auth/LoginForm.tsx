"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Controller, useForm } from "react-hook-form"
import { z } from "zod"
import { login } from "@/actions/auth"
import { zBodyLoginLoginAccessToken } from "@/client/zod.gen"
import { PasswordInput } from "@/components/Common/PasswordInput"
import { Button } from "@/components/ui/button"
import {
  Field,
  FieldError,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import useCustomToast from "@/hooks/useCustomToast"
import { formError } from "@/lib/form-errors"

const formSchema = z.object({
  username: z.email(),
  password: zBodyLoginLoginAccessToken.shape.password.min(1),
})

type FormData = z.infer<typeof formSchema>

export function LoginForm() {
  const router = useRouter()
  const { showErrorToast } = useCustomToast()
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema, { error: formError }),
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
        <Controller
          control={form.control}
          name="username"
          render={({ field, fieldState }) => (
            <Field data-invalid={fieldState.invalid}>
              <FieldLabel htmlFor={field.name}>Email</FieldLabel>
              <Input
                {...field}
                id={field.name}
                data-testid="email-input"
                placeholder="user@example.com"
                type="email"
                aria-invalid={fieldState.invalid}
              />
              {fieldState.error && (
                <FieldError className="text-xs" errors={[fieldState.error]} />
              )}
            </Field>
          )}
        />

        <Controller
          control={form.control}
          name="password"
          render={({ field, fieldState }) => (
            <Field data-invalid={fieldState.invalid}>
              <div className="flex items-center">
                <FieldLabel htmlFor={field.name}>Password</FieldLabel>
                <Link
                  href="/recover-password"
                  className="ml-auto text-sm underline-offset-4 hover:underline"
                >
                  Forgot your password?
                </Link>
              </div>
              <PasswordInput
                {...field}
                id={field.name}
                data-testid="password-input"
                placeholder="Password"
                aria-invalid={fieldState.invalid}
              />
              {fieldState.error && (
                <FieldError className="text-xs" errors={[fieldState.error]} />
              )}
            </Field>
          )}
        />

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
