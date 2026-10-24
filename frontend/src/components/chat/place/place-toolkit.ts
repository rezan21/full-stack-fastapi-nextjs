import { defineToolkit } from "@assistant-ui/react"
import { zPlace } from "@/client/zod.gen"
import { FLY_TO_TOOL, flyTo, type Place } from "@/lib/place-tool"
import { FlyToToolNote } from "./FlyToToolNote"

// The map tool, which moves the map the user is looking at to a place.
export function placeToolkit(show: (place: Place) => void) {
  return defineToolkit({
    [FLY_TO_TOOL]: {
      type: "frontend",
      parameters: zPlace,
      execute: (place) => flyTo(place, show),
      render: FlyToToolNote,
    },
  })
}
