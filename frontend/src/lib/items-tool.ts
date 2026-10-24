import { z } from "zod"

export const LIST_ITEMS_TOOL = "list_items"

const itemsResultSchema = z.object({
  count: z.number(),
  items: z.array(
    z.object({
      id: z.string(),
      title: z.string(),
      description: z.string().nullable(),
    }),
  ),
})

export type ItemsResult = z.infer<typeof itemsResultSchema>

// Reads JSON text, or undefined when it is not JSON.
function parseJson(text: string): unknown {
  try {
    return JSON.parse(text)
  } catch {
    return undefined
  }
}

// Returns the items the tool found, or undefined when its result is missing or not the expected shape.
export function parseItemsResult(result: unknown): ItemsResult | undefined {
  const items = itemsResultSchema.safeParse(
    typeof result === "string" ? parseJson(result) : result,
  )
  return items.success ? items.data : undefined
}
