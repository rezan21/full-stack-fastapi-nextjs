"use client"

import { ArrowUp, Square } from "lucide-react"
import { type FormEvent, type KeyboardEvent, useState } from "react"
import {
  InputGroup,
  InputGroupAddon,
  InputGroupButton,
  InputGroupText,
  InputGroupTextarea,
} from "@/components/ui/input-group"
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
  const [text, setText] = useState("")
  const length = text.trim().length
  const isTooLong = length > CHAT_MESSAGE_MAX_LENGTH
  const showCounter = length >= CHAT_MESSAGE_MAX_LENGTH * COUNTER_FROM
  const canSend = chatMessageSchema.safeParse(text).success

  const submit = async () => {
    const message = chatMessageSchema.safeParse(text)
    if (!message.success || isRunning) return
    setText("")
    const accepted = await onSend(message.data)
    if (!accepted) setText((current) => current || message.data)
  }

  const onSubmit = (event: FormEvent) => {
    event.preventDefault()
    submit()
  }

  const onKeyDown = (event: KeyboardEvent) => {
    if (
      event.key === "Enter" &&
      !event.shiftKey &&
      !event.nativeEvent.isComposing
    ) {
      event.preventDefault()
      submit()
    }
  }

  return (
    <form onSubmit={onSubmit}>
      <InputGroup>
        <InputGroupTextarea
          aria-label="Message"
          className="max-h-48 min-w-0 overflow-y-auto wrap-anywhere"
          aria-invalid={isTooLong}
          placeholder="Ask anything"
          rows={1}
          value={text}
          onChange={(event) => setText(event.target.value)}
          onKeyDown={onKeyDown}
        />
        <InputGroupAddon align="block-end">
          {showCounter && (
            <InputGroupText className={cn(isTooLong && "text-destructive")}>
              {length.toLocaleString("en-US")} /{" "}
              {CHAT_MESSAGE_MAX_LENGTH.toLocaleString("en-US")}
            </InputGroupText>
          )}
          {isRunning ? (
            <InputGroupButton
              type="button"
              variant="outline"
              size="icon-sm"
              className="ml-auto"
              aria-label="Stop"
              onClick={onStop}
            >
              <Square />
            </InputGroupButton>
          ) : (
            <InputGroupButton
              type="submit"
              variant="default"
              size="icon-sm"
              className="ml-auto"
              aria-label="Send"
              disabled={!canSend}
            >
              <ArrowUp />
            </InputGroupButton>
          )}
        </InputGroupAddon>
      </InputGroup>
    </form>
  )
}
