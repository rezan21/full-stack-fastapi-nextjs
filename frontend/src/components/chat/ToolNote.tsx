import type { ToolCallMessagePartStatus } from "@assistant-ui/react"
import type { ReactNode } from "react"
import { ShimmerLabel } from "@/components/assistant-ui/elements/surfaces"

// A one-line status for a tool call: what it is doing, then what it did.
export function ToolNote({
  status,
  running,
  done,
  icon,
}: {
  status: ToolCallMessagePartStatus
  running: string
  done: string
  icon?: ReactNode
}) {
  const settled = status.type === "complete" || status.type === "incomplete"
  return (
    <span className="inline-flex items-center gap-1.5 text-muted-foreground">
      {icon}
      <ShimmerLabel active={!settled}>{settled ? done : running}</ShimmerLabel>
    </span>
  )
}
