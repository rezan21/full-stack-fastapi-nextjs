import { z } from "zod"

export const itemFormSchema = z.object({
  title: z.string().min(1, { message: "Title is required" }),
  description: z.string().optional(),
})

export type ItemFormData = z.infer<typeof itemFormSchema>
