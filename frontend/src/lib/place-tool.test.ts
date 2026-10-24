import { describe, expect, test } from "bun:test"
import { flyTo, type Place } from "@/lib/place-tool"

const LONDON = { place: "London", lat: 51.5, lng: -0.12 }

describe("flyTo", () => {
  test("shows the place and tells the agent where the map is", () => {
    const shown: Place[] = []

    const answer = flyTo(LONDON, (place) => shown.push(place))

    expect(shown).toEqual([LONDON])
    expect(answer).toBe("The map now shows London.")
  })
})
