import { describe, expect, test } from "bun:test"
import { flyTo, type Place } from "@/lib/place"

const LONDON = { place: "London", lat: 51.5, lng: -0.12 }

describe("flyTo", () => {
  test("shows the place and tells the agent where the map is", () => {
    const shown: Place[] = []

    const answer = flyTo(LONDON, (place) => shown.push(place))

    expect(shown).toEqual([LONDON])
    expect(answer).toBe("The map now shows London.")
  })

  test("leaves the map alone and says so when the place is not valid", () => {
    const shown: Place[] = []
    const invalid = [
      {},
      { ...LONDON, lat: 91 },
      { ...LONDON, lng: -181 },
      { ...LONDON, place: "" },
      { ...LONDON, place: "x".repeat(81) },
      { ...LONDON, lat: "51.5" },
      null,
    ]

    for (const args of invalid) {
      const answer = flyTo(args, (place) => shown.push(place))
      expect(answer).toStartWith("The map was not moved")
    }

    expect(shown).toEqual([])
  })
})
