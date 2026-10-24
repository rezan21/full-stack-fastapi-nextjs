import type { Place } from "@/lib/place"
import { ChatPanel, type ChatState } from "./ChatPanel"
import { PlaceMap } from "./PlaceMap"

// A conversation beside the map the assistant can move.
export function ChatWithMap({
  chat,
  shown,
  total,
  place,
}: {
  chat: ChatState
  shown: number
  total: number
  place?: Place
}) {
  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
      <ChatPanel chat={chat} shown={shown} total={total} />
      <PlaceMap place={place} />
    </div>
  )
}
