import { MapPin } from "lucide-react"
import type { Place } from "@/lib/place"

// A line saying the assistant is moving, or has moved, the map.
export function FlyToToolNote({
  isDone,
  place,
}: {
  isDone: boolean
  place?: Partial<Place>
}) {
  const name = place?.place ?? "the place"
  return (
    <span className="inline-flex items-center gap-1.5 text-muted-foreground">
      <MapPin className="size-3.5" />
      {isDone ? `Moved the map to ${name}` : `Moving the map to ${name}`}
    </span>
  )
}
