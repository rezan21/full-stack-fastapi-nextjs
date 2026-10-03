import type { z } from "zod"
import { zItemCreate } from "@/client/zod.gen"

export const itemFormSchema = zItemCreate

export type ItemFormData = z.infer<typeof itemFormSchema>
