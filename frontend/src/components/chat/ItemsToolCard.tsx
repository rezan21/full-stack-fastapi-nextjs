import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { parseItemsResult } from "@/lib/items-tool"

// What the assistant found when it looked up the user's items.
export function ItemsToolCard({
  isDone,
  result,
}: {
  isDone: boolean
  result?: unknown
}) {
  if (!isDone) {
    return (
      <span className="shimmer text-muted-foreground">
        Looking up your items
      </span>
    )
  }
  const found = parseItemsResult(result)
  if (!found) {
    return (
      <span className="text-muted-foreground">
        Your items could not be shown.
      </span>
    )
  }
  return (
    <Card size="sm">
      <CardHeader>
        <CardTitle>
          {found.count === 1 ? "1 item" : `${found.count} items`}
        </CardTitle>
        {found.count === 0 && (
          <CardDescription>You have no items yet</CardDescription>
        )}
        {found.count > found.items.length && (
          <CardDescription>
            Showing the first {found.items.length}
          </CardDescription>
        )}
      </CardHeader>
      {found.items.length > 0 && (
        <CardContent>
          <ul className="flex flex-col gap-1">
            {found.items.map((item) => (
              <li key={item.id}>
                <span className="font-medium">{item.title}</span>
                {item.description && (
                  <span className="text-muted-foreground">
                    {" "}
                    · {item.description}
                  </span>
                )}
              </li>
            ))}
          </ul>
        </CardContent>
      )}
    </Card>
  )
}
