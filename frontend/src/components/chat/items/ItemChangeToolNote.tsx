"use client"

import type { ToolCallMessagePartProps } from "@assistant-ui/react"
import {
  useAgUiInterrupts,
  useAgUiSubmitInterruptResponses,
} from "@assistant-ui/react-ag-ui"
import { ToolNote } from "@/components/chat/ToolNote"
import {
  CREATE_ITEM_TOOL,
  itemFormDefaults,
  parseItemChange,
  UPDATE_ITEM_TOOL,
} from "@/lib/items-tool"
import { ItemForm } from "./ItemForm"

const RUNNING_LABELS: Record<string, string> = {
  [CREATE_ITEM_TOOL]: "Adding an item",
  [UPDATE_ITEM_TOOL]: "Updating an item",
}

// What the assistant is doing to an item: the form it needs filled in, then what it did.
export function ItemChangeToolNote({
  toolName,
  toolCallId,
  status,
  result,
}: Pick<
  ToolCallMessagePartProps,
  "toolName" | "toolCallId" | "status" | "result"
>) {
  const interrupt = useAgUiInterrupts().find((i) => i.toolCallId === toolCallId)
  const submitInterruptResponses = useAgUiSubmitInterruptResponses()

  if (interrupt) {
    return (
      <ItemForm
        heading={interrupt.message ?? "Item details"}
        defaultValues={itemFormDefaults(interrupt.responseSchema)}
        onSubmit={(payload) =>
          submitInterruptResponses([
            { interruptId: interrupt.id, status: "resolved", payload },
          ])
        }
        onCancel={() =>
          submitInterruptResponses([
            { interruptId: interrupt.id, status: "cancelled" },
          ])
        }
      />
    )
  }
  return (
    <ToolNote
      status={status}
      running={RUNNING_LABELS[toolName]}
      done={
        parseItemChange(result)?.message ?? "The item could not be changed."
      }
    />
  )
}
