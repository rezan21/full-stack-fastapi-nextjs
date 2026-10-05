import { z } from "zod"
import { zChatRun, zItemCreate } from "@/client/zod.gen"
import { CHAT_MESSAGE_MAX_LENGTH } from "@/lib/config"

export const itemFormSchema = zItemCreate

const messageTooLong = `The message can be at most ${CHAT_MESSAGE_MAX_LENGTH} characters.`

export const chatMessageSchema = z
  .string()
  .trim()
  .max(CHAT_MESSAGE_MAX_LENGTH, { error: messageTooLong })
  .min(1)

export const chatRunSchema = zChatRun.refine(
  (run) => {
    const newest = run.messages.findLast((message) => message.role === "user")
    return (
      typeof newest?.content !== "string" ||
      newest.content.length <= CHAT_MESSAGE_MAX_LENGTH
    )
  },
  { error: messageTooLong, path: ["messages"] },
)

export type ItemFormData = z.infer<typeof itemFormSchema>

// Adds a password confirmation check to a schema.
export function withPasswordConfirmation<
  Shape extends z.core.$ZodShape,
  Field extends keyof Shape & string,
>(schema: z.ZodObject<Shape>, field: Field) {
  const confirmation = z
    .string()
    .min(1, { error: "Password confirmation is required" })
  return schema.extend({ confirm_password: confirmation }).refine(
    (data) => {
      const values = data as Record<string, unknown>
      return values[field] === values.confirm_password
    },
    { error: "The passwords don't match", path: ["confirm_password"] },
  )
}
