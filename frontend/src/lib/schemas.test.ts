import { describe, expect, test } from "bun:test"
import { zNewPassword } from "@/client/zod.gen"
import { formError } from "@/lib/form-errors"
import { withPasswordConfirmation } from "@/lib/schemas"

const reset = withPasswordConfirmation(
  zNewPassword.pick({ new_password: true }),
  "new_password",
)
const valid = { new_password: "password123" }

function messages(schema: typeof reset, value: object) {
  const result = schema.safeParse(value, { error: formError })
  return result.success
    ? []
    : result.error.issues.map((issue) => [issue.path.join("."), issue.message])
}

describe("withPasswordConfirmation", () => {
  test("accepts matching passwords and keeps the contract's rules", () => {
    expect(
      reset.safeParse({ ...valid, confirm_password: "password123" }).success,
    ).toBe(true)
    expect(
      messages(reset, { new_password: "short", confirm_password: "short" }),
    ).toEqual([["new_password", "New password must be at least 8 characters"]])
  })

  test("reports a mismatch on the confirmation field", () => {
    expect(
      messages(reset, { ...valid, confirm_password: "something else" }),
    ).toEqual([["confirm_password", "The passwords don't match"]])
  })

  test("reports an empty confirmation as required", () => {
    expect(messages(reset, { ...valid, confirm_password: "" })).toContainEqual([
      "confirm_password",
      "Password confirmation is required",
    ])
  })

  test("compares whichever field it is given", () => {
    expect(
      messages(reset, { new_password: "password123", confirm_password: "x" }),
    ).toEqual([["confirm_password", "The passwords don't match"]])
    expect(
      reset.safeParse({
        new_password: "password123",
        confirm_password: "password123",
      }).success,
    ).toBe(true)
  })
})
