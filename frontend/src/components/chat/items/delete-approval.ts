import type { ApprovalState } from "@/components/assistant-ui/elements/approval-card"
import { parseItemChange } from "@/lib/items-tool"

export type DeleteApprovalDisplay = {
  state: ApprovalState
  statusLabel?: string
}

// Works out a delete approval card's state from the approval gate and the delete tool's result.
export function deleteApprovalDisplay(
  approval: { approved?: boolean; resolution?: string } | undefined,
  result: unknown,
): DeleteApprovalDisplay {
  const outcome = parseItemChange(result)
  const done: DeleteApprovalDisplay = outcome
    ? { state: "done", statusLabel: outcome.message }
    : { state: "running" }
  if (!approval) return done
  if (approval.approved === undefined) {
    return approval.resolution
      ? { state: "denied", statusLabel: "No answer, nothing deleted" }
      : { state: "request" }
  }
  if (!approval.approved) return { state: "denied", statusLabel: "Kept" }
  return done
}
