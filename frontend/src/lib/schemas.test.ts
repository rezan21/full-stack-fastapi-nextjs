import { describe, expect, test } from "bun:test"
import { zNewPassword } from "@/client/zod.gen"
import { CHAT_MESSAGE_MAX_LENGTH } from "@/lib/config"
import { formError } from "@/lib/form-errors"
import {
  chatMessageSchema,
  chatRunSchema,
  withPasswordConfirmation,
} from "@/lib/schemas"

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

const TOO_LONG = `The message can be at most ${CHAT_MESSAGE_MAX_LENGTH} characters.`

describe("chatMessageSchema", () => {
  test("accepts text up to the limit and trims it", () => {
    expect(
      chatMessageSchema.safeParse("x".repeat(CHAT_MESSAGE_MAX_LENGTH)).success,
    ).toBe(true)
    expect(chatMessageSchema.parse("  hello \n")).toBe("hello")
  })

  test("refuses blank text and text over the limit", () => {
    expect(chatMessageSchema.safeParse("  \n ").success).toBe(false)
    const result = chatMessageSchema.safeParse(
      "x".repeat(CHAT_MESSAGE_MAX_LENGTH + 1),
    )
    expect(result.success).toBe(false)
    expect(result.error?.issues[0].message).toBe(TOO_LONG)
  })
})

describe("chatRunSchema", () => {
  const run = (...messages: { role: string; content?: unknown }[]) => ({
    threadId: "t-1",
    runId: "r-1",
    messages,
  })
  const long = "x".repeat(CHAT_MESSAGE_MAX_LENGTH + 1)

  test("refuses a run whose newest user message is over the limit", () => {
    const result = chatRunSchema.safeParse(run({ role: "user", content: long }))
    expect(result.success).toBe(false)
    expect(result.error?.issues[0]).toMatchObject({
      code: "custom",
      message: TOO_LONG,
    })
  })

  test("lets long earlier messages and assistant replies through", () => {
    const history = run(
      { role: "user", content: long },
      { role: "assistant", content: long },
      { role: "user", content: "a short follow-up" },
    )
    expect(chatRunSchema.safeParse(history).success).toBe(true)
  })

  test("leaves a run with nothing to measure to the API", () => {
    expect(chatRunSchema.safeParse(run()).success).toBe(true)
    expect(chatRunSchema.safeParse(run({ role: "user" })).success).toBe(true)
    expect(
      chatRunSchema.safeParse(
        run({ role: "user", content: [{ type: "text" }] }),
      ).success,
    ).toBe(true)
  })

  test("still enforces the shape the contract describes", () => {
    expect(chatRunSchema.safeParse({ runId: "r", messages: [] }).success).toBe(
      false,
    )
  })
})
