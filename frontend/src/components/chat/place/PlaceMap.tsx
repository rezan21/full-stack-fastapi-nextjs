import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import type { Place } from "@/lib/place-tool"
import { WORLD_LAND_POINTS } from "@/lib/world-land"

const MERIDIANS = [-150, -120, -90, -60, -30, 0, 30, 60, 90, 120, 150]
const PARALLELS = [-60, -30, 0, 30, 60]

// A flat map that marks the place the assistant last took the user to.
export function PlaceMap({ place }: { place?: Place }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Map</CardTitle>
        <CardDescription>
          {place
            ? `${place.place} (${place.lat.toFixed(2)}, ${place.lng.toFixed(2)})`
            : "Ask the assistant to take you somewhere"}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <svg
          viewBox="0 0 360 180"
          role="img"
          aria-label={place ? `Map showing ${place.place}` : "Map"}
          className="w-full rounded-lg bg-muted"
        >
          {WORLD_LAND_POINTS.map((points) => (
            <polygon
              key={points}
              points={points}
              className="fill-foreground/15"
            />
          ))}
          {MERIDIANS.map((lng) => (
            <line
              key={`m${lng}`}
              x1={lng + 180}
              x2={lng + 180}
              y1={0}
              y2={180}
              className="stroke-border"
            />
          ))}
          {PARALLELS.map((lat) => (
            <line
              key={`p${lat}`}
              x1={0}
              x2={360}
              y1={90 - lat}
              y2={90 - lat}
              className="stroke-border"
            />
          ))}
          {place && (
            <g
              data-testid="map-pin"
              className="fill-primary transition-transform duration-700"
              style={{
                transform: `translate(${place.lng + 180}px, ${90 - place.lat}px)`,
              }}
            >
              <circle r={9} className="fill-primary/20" />
              <circle r={4} />
            </g>
          )}
        </svg>
      </CardContent>
    </Card>
  )
}
