import type { ToolCallMessagePartProps } from "@assistant-ui/react"
import { MapPin } from "lucide-react"
import { ToolNote } from "@/components/chat/ToolNote"
import type { Place } from "@/lib/place-tool"

// A line saying the assistant is moving, or has moved, the map.
export function FlyToToolNote({
  status,
  args,
}: Pick<ToolCallMessagePartProps<Partial<Place>>, "status" | "args">) {
  const name = args.place ?? "the place"
  return (
    <ToolNote
      status={status}
      icon={<MapPin className="size-3.5" />}
      running={`Moving the map to ${name}`}
      done={`Moved the map to ${name}`}
    />
  )
}
