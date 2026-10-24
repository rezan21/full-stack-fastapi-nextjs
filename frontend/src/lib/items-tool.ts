import { z } from "zod"
import { zAgentItemChange, zAgentItems, zToolName } from "@/client/zod.gen"
import type { ItemFormData } from "@/lib/schemas"
import { parseJson } from "@/lib/utils"

export const LIST_ITEMS_TOOL = zToolName.enum.list_items
export const CREATE_ITEM_TOOL = zToolName.enum.create_item
export const UPDATE_ITEM_TOOL = zToolName.enum.update_item
export const DELETE_ITEM_TOOL = zToolName.enum.delete_item

export type ItemsResult = z.infer<typeof zAgentItems>

// Returns a tool's result in the schema's shape, or undefined when it is missing or not that shape.
function parseResult<Schema extends z.ZodType>(
  schema: Schema,
  result: unknown,
): z.output<Schema> | undefined {
  const parsed = schema.safeParse(
    typeof result === "string" ? parseJson(result) : result,
  )
  return parsed.success ? parsed.data : undefined
}

// Returns the items the list tool found, or undefined when its result is missing or not that shape.
export function parseItemsResult(result: unknown): ItemsResult | undefined {
  return parseResult(zAgentItems, result)
}

// Returns what a create, update or delete tool did, or undefined when its result is missing or not that shape.
export function parseItemChange(result: unknown) {
  return parseResult(zAgentItemChange, result)
}

const formDefaultsSchema = z.object({
  properties: z.object({
    title: z.object({ default: z.string().nullish() }).optional(),
    description: z.object({ default: z.string().nullish() }).optional(),
  }),
})

// Returns the values an item form starts with, taken from the interrupt's form schema.
export function itemFormDefaults(
  responseSchema: Record<string, unknown> | undefined,
): ItemFormData {
  const form = formDefaultsSchema.safeParse(responseSchema)
  const properties = form.success ? form.data.properties : undefined
  return {
    title: properties?.title?.default ?? "",
    description: properties?.description?.default ?? "",
  }
}
