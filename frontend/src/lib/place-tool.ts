import type { z } from "zod"
import { type zPlace, zToolName } from "@/client/zod.gen"

export const FLY_TO_TOOL = zToolName.enum.fly_to

export type Place = z.infer<typeof zPlace>

// Shows the place on the map and returns what to tell the agent.
export function flyTo(place: Place, show: (place: Place) => void): string {
  show(place)
  return `The map now shows ${place.place}.`
}
