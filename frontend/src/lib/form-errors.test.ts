import { describe, expect, test } from "bun:test"
import { z } from "zod"
import { formError } from "@/lib/form-errors"

function messageFor(schema: z.ZodType, value: unknown) {
  const result = schema.safeParse(value, { error: formError })
  return result.success ? undefined : result.error.issues[0].message
}

describe("formError", () => {
  test("calls an empty string a missing value", () => {
    const schema = z.object({ full_name: z.string().min(1) })
    expect(messageFor(schema, { full_name: "" })).toBe("Full name is required")
  })

  test("states the minimum for a non-empty string that is too short", () => {
    const schema = z.object({ password: z.string().min(8) })
    expect(messageFor(schema, { password: "short" })).toBe(
      "Password must be at least 8 characters",
    )
  })

  test("states the maximum for a string that is too long", () => {
    const schema = z.object({ title: z.string().max(3) })
    expect(messageFor(schema, { title: "toolong" })).toBe(
      "Title must be at most 3 characters",
    )
  })

  test("labels the field by the last segment of its path", () => {
    const schema = z.object({
      body: z.object({ new_password: z.string().min(8) }),
    })
    expect(messageFor(schema, { body: { new_password: "x" } })).toBe(
      "New password must be at least 8 characters",
    )
  })

  test("leaves every other issue to the default message", () => {
    expect(messageFor(z.object({ email: z.email() }), { email: "nope" })).toBe(
      "Invalid email address",
    )
  })
})
