import { z } from "zod"

export const FLY_TO_TOOL = "fly_to"

export const placeSchema = z.object({
  place: z.string().min(1).max(80),
  lat: z.number().min(-90).max(90),
  lng: z.number().min(-180).max(180),
})

export type Place = z.infer<typeof placeSchema>

// Shows the place the agent named and returns what to tell the agent.
export function flyTo(args: unknown, show: (place: Place) => void): string {
  const place = placeSchema.safeParse(args)
  if (!place.success) {
    return "The map was not moved: the place's name or coordinates are not valid."
  }
  show(place.data)
  return `The map now shows ${place.data.place}.`
}
