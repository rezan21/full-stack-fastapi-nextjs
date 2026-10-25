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
  argsText,
  result,
}: {
  status: ToolCallMessagePartStatus
  argsText: string
  result?: unknown
}) {
  const found = parseItemsResult(result)
  const count = found && (found.count === 1 ? "1 item" : `${found.count} items`)
  return (
    <div className="flex flex-col gap-2">
      <ToolNote
        status={status}
        running="Looking up your items"
        done="Looked up your items"
        query={count}
        request={argsText}
        result={found?.data.map((item) => item.title).join(", ") ?? ""}
        failure={
          status.type === "complete" && !found
            ? "Your items could not be shown."
            : undefined
        }
      />
      {found && (
        <Card size="sm">
          <CardHeader>
            <CardTitle>{count}</CardTitle>
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
      )}
    </div>
  )
}
