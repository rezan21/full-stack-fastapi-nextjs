import { describe, expect, test } from "bun:test"
import { zNewPassword, zUserRegister } from "@/client/zod.gen"
import { formError } from "@/lib/form-errors"
import { withPasswordConfirmation } from "@/lib/schemas"

const signup = withPasswordConfirmation(zUserRegister, "password")
const reset = withPasswordConfirmation(
  zNewPassword.pick({ new_password: true }),
  "new_password",
)
const valid = {
  email: "user@example.com",
  password: "password123",
  full_name: "A User",
}

function messages(schema: typeof signup | typeof reset, value: object) {
  const result = schema.safeParse(value, { error: formError })
  return result.success
    ? []
    : result.error.issues.map((issue) => [issue.path.join("."), issue.message])
}

describe("withPasswordConfirmation", () => {
  test("accepts matching passwords and keeps the contract's rules", () => {
    expect(
      signup.safeParse({ ...valid, confirm_password: "password123" }).success,
    ).toBe(true)
    expect(
      messages(signup, {
        ...valid,
        password: "short",
        confirm_password: "short",
      }),
    ).toEqual([["password", "Password must be at least 8 characters"]])
  })

  test("reports a mismatch on the confirmation field", () => {
    expect(
      messages(signup, { ...valid, confirm_password: "something else" }),
    ).toEqual([["confirm_password", "The passwords don't match"]])
  })

  test("reports an empty confirmation as required", () => {
    expect(messages(signup, { ...valid, confirm_password: "" })).toContainEqual(
      ["confirm_password", "Password confirmation is required"],
    )
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
