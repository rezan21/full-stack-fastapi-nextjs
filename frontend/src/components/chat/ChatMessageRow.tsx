"use client"

import {
  groupPartByType,
  MessagePrimitive,
  useAuiState,
} from "@assistant-ui/react"
import {
  ReasoningContent,
  ReasoningRoot,
  ReasoningText,
  ReasoningTrigger,
} from "@/components/assistant-ui/elements/reasoning.aui"
import { ThinkingIndicator } from "@/components/assistant-ui/elements/thinking-indicator"
import { ToolFallback } from "@/components/assistant-ui/elements/tool-fallback.aui"
import {
  ToolGroupContent,
  ToolGroupRoot,
  ToolGroupTrigger,
} from "@/components/assistant-ui/elements/tool-group.aui"
import { Bubble, BubbleContent } from "@/components/ui/bubble"
import { Message, MessageContent } from "@/components/ui/message"
import { AssistantText } from "./AssistantText"
import { MessageActionBar } from "./MessageActionBar"

const groupBy = groupPartByType({
  reasoning: ["group-reasoning"],
  "tool-call": ["group-tool"],
  "standalone-tool-call": [],
})

// One message of the conversation, read from the message the thread provides.
export function ChatMessageRow() {
  const isUser = useAuiState((s) => s.message.role === "user")
  const isBlank = useAuiState(
    (s) =>
      s.message.status?.type !== "running" &&
      !s.message.parts.some(
        (part) =>
          part.type === "tool-call" ||
          part.type === "reasoning" ||
          (part.type === "text" && part.text !== ""),
      ),
  )
  if (isBlank) return null

  return (
    <MessagePrimitive.Root
      render={<Message align={isUser ? "end" : "start"} />}
    >
      <MessageContent>
        {isUser ? <UserParts /> : <AssistantParts />}
        <MessageActionBar />
      </MessageContent>
    </MessagePrimitive.Root>
  )
}

// What the user wrote.
function UserParts() {
  return (
    <MessagePrimitive.Parts>
      {({ part }) =>
        part.type === "text" && part.text ? (
          <Bubble align="end">
            <BubbleContent className="whitespace-pre-wrap">
              {part.text}
            </BubbleContent>
          </Bubble>
        ) : null
      }
    </MessagePrimitive.Parts>
  )
}

// What the assistant thought, said and did, with its tool calls folded away unless they have a UI of their own.
function AssistantParts() {
  return (
    <MessagePrimitive.GroupedParts groupBy={groupBy}>
      {({ part, children }) => {
        switch (part.type) {
          case "group-reasoning": {
            const running = part.status.type === "running"
            return (
              <ReasoningRoot variant="ghost" streaming={running}>
                <ReasoningTrigger active={running} />
                <ReasoningContent aria-busy={running}>
                  <ReasoningText>{children}</ReasoningText>
                </ReasoningContent>
              </ReasoningRoot>
            )
          }
          case "group-tool":
            return (
              <ToolGroupRoot variant="ghost">
                <ToolGroupTrigger
                  count={part.indices.length}
                  active={part.status.type === "running"}
                />
                <ToolGroupContent>{children}</ToolGroupContent>
              </ToolGroupRoot>
            )
          case "reasoning":
            return <AssistantText />
          case "text":
            return part.text ? (
              <Bubble variant="ghost">
                <BubbleContent>
                  <AssistantText />
                </BubbleContent>
              </Bubble>
            ) : null
          case "tool-call":
            return part.toolUI ?? <ToolFallback {...part} />
          case "indicator":
            return <ThinkingIndicator label="Thinking" />
          default:
            return null
        }
      }}
    </MessagePrimitive.GroupedParts>
  )
}
