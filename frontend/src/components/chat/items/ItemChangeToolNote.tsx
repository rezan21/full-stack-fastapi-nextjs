"use client"

import type { ToolCallMessagePartProps } from "@assistant-ui/react"
import { useAgUiInterrupts } from "@assistant-ui/react-ag-ui"
import { InterruptForm } from "@/components/chat/InterruptForm"
import { ToolNote } from "@/components/chat/ToolNote"
import {
  CREATE_ITEM_TOOL,
  itemChangeFailure,
  itemProblem,
  parseItemChange,
  UPDATE_ITEM_TOOL,
} from "@/lib/items-tool"

const LABELS: Record<string, { running: string; done: string }> = {
  [CREATE_ITEM_TOOL]: { running: "Adding an item", done: "Added an item" },
  [UPDATE_ITEM_TOOL]: { running: "Updating an item", done: "Updated an item" },
}

// What the assistant is doing to an item: the form it needs filled in, then what it did.
export function ItemChangeToolNote({
  toolName,
  toolCallId,
  args,
  argsText,
  status,
  result,
}: Pick<
  ToolCallMessagePartProps<{ title?: string }>,
  "toolName" | "toolCallId" | "args" | "argsText" | "status" | "result"
>) {
  const interrupt = useAgUiInterrupts().find((i) => i.toolCallId === toolCallId)

  if (interrupt)
    return <InterruptForm interrupt={interrupt} problem={itemProblem} />
  const change = parseItemChange(result)
  return (
    <ToolNote
      status={status}
      running={LABELS[toolName].running}
      done={LABELS[toolName].done}
      query={change?.item?.title ?? args.title}
      request={argsText}
      result={change?.message ?? ""}
      failure={
        status.type === "complete" ? itemChangeFailure(change) : undefined
      }
    />
  )
}
