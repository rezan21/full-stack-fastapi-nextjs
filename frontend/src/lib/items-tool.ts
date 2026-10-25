import type { z } from "zod"
import { zAgentItemChange, zAgentItems, zToolName } from "@/client/zod.gen"
import { formError } from "@/lib/form-errors"
import { itemFormSchema } from "@/lib/schemas"
import { parseJson } from "@/lib/utils"

export const LIST_ITEMS_TOOL = zToolName.enum.list_items
export const CREATE_ITEM_TOOL = zToolName.enum.create_item
export const UPDATE_ITEM_TOOL = zToolName.enum.update_item
export const DELETE_ITEM_TOOL = zToolName.enum.delete_item

export type ItemsResult = z.infer<typeof zAgentItems>
export type ItemChange = z.infer<typeof zAgentItemChange>

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

// Returns why a finished create or update changed nothing, or undefined when it changed the item.
export function itemChangeFailure(
  change: ItemChange | undefined,
): string | undefined {
  if (!change) return "The item could not be changed."
  return change.changed ? undefined : change.message
}

// Returns why an answer is not a valid item, or undefined when it is one.
export function itemProblem(answer: unknown): string | undefined {
  const item = itemFormSchema.safeParse(answer, { error: formError })
  return item.success ? undefined : item.error.issues[0]?.message
}
