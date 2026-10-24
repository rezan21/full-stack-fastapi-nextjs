"use client"

import type { ToolCallMessagePartProps } from "@assistant-ui/react"
import { Trash2 } from "lucide-react"
import { useState } from "react"
import { ApprovalCard } from "@/components/assistant-ui/elements/approval-card"
import { deleteApprovalDisplay } from "./delete-approval"

// Asks the user to approve deleting one of their items before the assistant does it.
export function DeleteItemToolCard({
  approval,
  result,
  respondToApproval,
}: Pick<
  ToolCallMessagePartProps,
  "approval" | "result" | "respondToApproval"
>) {
  const [error, setError] = useState<string>()
  const display = deleteApprovalDisplay(approval, result)

  const answer = async (approved: boolean) => {
    setError(undefined)
    try {
      await respondToApproval({ approved })
    } catch {
      setError("Your answer could not be recorded. Try again.")
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <ApprovalCard
        state={display.state}
        title="Delete an item?"
        subtitle="The assistant wants to delete one of your items"
        description={approval?.prompt}
        variant="destructive"
        icon={<Trash2 className="size-4" />}
        allowOnceLabel="Delete"
        denyLabel="Keep"
        statusLabel={display.statusLabel}
        onAllowOnce={() => void answer(true)}
        onDeny={() => void answer(false)}
      />
      {error && (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      )}
    </div>
  )
}
