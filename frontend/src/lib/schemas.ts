import { z } from "zod"
import { zItemCreate } from "@/client/zod.gen"

export const itemFormSchema = zItemCreate

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
