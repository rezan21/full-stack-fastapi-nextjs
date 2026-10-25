"use client"

import type { ToolCallMessagePartStatus } from "@assistant-ui/react"
import { CircleAlert } from "lucide-react"
import { useState } from "react"
import { ToolCall } from "@/components/assistant-ui/elements/tool-call"

const NO_QUERY = "…"

// A tool call's line: what it is doing, then what it did, or why it did nothing.
export function ToolNote({
  status,
  running,
  done,
  query,
  request,
  result,
  failure,
}: {
  status: ToolCallMessagePartStatus
  running: string
  done: string
  query?: string
  request: string
  result: string
  failure?: string
}) {
  const [open, setOpen] = useState(false)
  const problem =
    status.type === "incomplete" ? `${running} (didn't finish)` : failure

  if (problem) {
    return (
      <span className="flex items-center gap-2 py-1 text-[13.5px] text-muted-foreground">
        <CircleAlert className="size-3.5 shrink-0 text-destructive" />
        {problem}
      </span>
    )
  }
  return (
    <ToolCall
      label={done}
      activeLabel={running}
      query={query || NO_QUERY}
      request={request}
      result={result}
      running={status.type !== "complete"}
      open={open}
      onOpenChange={setOpen}
    />
  )
}
