import type { ToolCallMessagePartStatus } from "@assistant-ui/react"
import { ToolNote } from "@/components/chat/ToolNote"
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
  status,
  result,
}: {
  status: ToolCallMessagePartStatus
  result?: unknown
}) {
  const found = parseItemsResult(result)
  if (!found) {
    return (
      <ToolNote
        status={status}
        running="Looking up your items"
        done="Your items could not be shown."
      />
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
        {found.count > found.data.length && (
          <CardDescription>
            Showing the first {found.data.length}
          </CardDescription>
        )}
      </CardHeader>
      {found.data.length > 0 && (
        <CardContent>
          <ul className="flex flex-col gap-1">
            {found.data.map((item) => (
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
