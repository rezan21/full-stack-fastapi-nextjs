"use client"

import { ComposerPrimitive, useAui, useAuiState } from "@assistant-ui/react"
import { ArrowUp, Square } from "lucide-react"
import type { FormEvent } from "react"
import {
  iconSwap,
  iconSwapIn,
  iconSwapOut,
  inkButton,
  mono,
  paper,
} from "@/components/assistant-ui/elements/surfaces"
import { CHAT_MESSAGE_MAX_LENGTH } from "@/lib/config"
import { chatMessageSchema } from "@/lib/schemas"
import { cn } from "@/lib/utils"

const COUNTER_FROM = 0.8

// Box for writing a message to the assistant.
export function ChatInput({
  isRunning,
  onSend,
  onStop,
}: {
  isRunning: boolean
  onSend: (text: string) => Promise<boolean>
  onStop: () => void
}) {
  const aui = useAui()
  const text = useAuiState((s) => s.composer.text)
  const length = text.trim().length
  const isTooLong = length > CHAT_MESSAGE_MAX_LENGTH
  const showCounter = length >= CHAT_MESSAGE_MAX_LENGTH * COUNTER_FROM
  const canSend = chatMessageSchema.safeParse(text).success

  const submit = async () => {
    const message = chatMessageSchema.safeParse(text)
    if (!message.success || isRunning) return
    aui.composer().setText("")
    const accepted = await onSend(message.data)
    if (!accepted && !aui.composer().getState().text) {
      aui.composer().setText(message.data)
    }
  }

  const onSubmit = (event: FormEvent) => {
    event.preventDefault()
    submit()
  }

  return (
    <ComposerPrimitive.Root
      onSubmit={onSubmit}
      className={cn(
        paper,
        "flex w-full flex-col gap-2 rounded-[24px] p-2.5 focus-within:ring-1 focus-within:ring-ring has-[[aria-invalid=true]]:border-destructive",
      )}
    >
      <ComposerPrimitive.Input
        aria-label="Message"
        aria-invalid={isTooLong}
        placeholder="Ask anything"
        rows={1}
        className="placeholder:text-muted-foreground max-h-48 min-h-11 w-full min-w-0 resize-none overflow-y-auto bg-transparent px-3 text-[15px] outline-none wrap-anywhere"
      />
      <div className="flex items-center">
        {showCounter && (
          <span
            className={cn(
              mono,
              "text-muted-foreground tabular-nums",
              isTooLong && "text-destructive",
            )}
          >
            {length.toLocaleString("en-US")} /{" "}
            {CHAT_MESSAGE_MAX_LENGTH.toLocaleString("en-US")}
          </span>
        )}
        <button
          type={isRunning ? "button" : "submit"}
          aria-label={isRunning ? "Stop" : "Send"}
          disabled={!isRunning && !canSend}
          onClick={isRunning ? onStop : undefined}
          className={cn(
            inkButton,
            "ms-auto grid size-8 place-items-center rounded-full disabled:pointer-events-none disabled:opacity-40",
          )}
        >
          <ArrowUp
            className={cn(
              iconSwap,
              "size-4",
              isRunning ? iconSwapOut : iconSwapIn,
            )}
          />
          <Square
            className={cn(
              iconSwap,
              "size-3 fill-current",
              isRunning ? iconSwapIn : iconSwapOut,
            )}
          />
        </button>
      </div>
    </ComposerPrimitive.Root>
  )
}
