import type { ToolCallMessagePartProps } from "@assistant-ui/react"
import { ToolNote } from "@/components/chat/ToolNote"
import type { Place } from "@/lib/place-tool"

// A line saying the assistant is moving, or has moved, the map.
export function FlyToToolNote({
  status,
  args,
  argsText,
  result,
}: Pick<
  ToolCallMessagePartProps<Partial<Place>>,
  "status" | "args" | "argsText" | "result"
>) {
  return (
    <ToolNote
      status={status}
      running="Moving the map"
      done="Moved the map"
      query={args.place}
      request={argsText}
      result={typeof result === "string" ? result : ""}
    />
  )
}
