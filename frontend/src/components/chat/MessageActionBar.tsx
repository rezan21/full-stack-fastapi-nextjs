"use client"

import { ActionBarPrimitive, AuiIf, useAuiState } from "@assistant-ui/react"
import { Check, Copy } from "lucide-react"
import { TooltipIconButton } from "@/components/assistant-ui/elements/tooltip-icon-button"
import { MessageFooter } from "@/components/ui/message"

// Actions under a message.
export function MessageActionBar() {
  const isUser = useAuiState((s) => s.message.role === "user")
  const hasText = useAuiState((s) =>
    s.message.parts.some((part) => part.type === "text" && part.text !== ""),
  )
  if (!hasText) return null

  return (
    <MessageFooter className="h-6">
      <ActionBarPrimitive.Root
        hideWhenRunning={!isUser}
        className="flex gap-1 text-muted-foreground opacity-0 transition-opacity focus-within:opacity-100 group-hover/message:opacity-100 pointer-coarse:opacity-100"
      >
        <TooltipIconButton tooltip="Copy" render={<ActionBarPrimitive.Copy />}>
          <AuiIf condition={(s) => s.message.isCopied}>
            <Check />
          </AuiIf>
          <AuiIf condition={(s) => !s.message.isCopied}>
            <Copy />
          </AuiIf>
        </TooltipIconButton>
      </ActionBarPrimitive.Root>
    </MessageFooter>
  )
}
