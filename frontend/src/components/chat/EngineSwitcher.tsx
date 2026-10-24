import Link from "next/link"
import { Button } from "@/components/ui/button"

const ENGINES = [
  { label: "Current", path: "" },
  { label: "CopilotKit", path: "/copilotkit" },
  { label: "assistant-ui", path: "/assistant-ui" },
]

// Links to the same conversation in each of the chat implementations.
export function EngineSwitcher({
  conversationId,
  current,
}: {
  conversationId: string
  current: string
}) {
  return (
    <div className="flex gap-2">
      {ENGINES.map((engine) => (
        <Button
          key={engine.label}
          variant={engine.path === current ? "secondary" : "outline"}
          render={<Link href={`/chat/${conversationId}${engine.path}`} />}
          nativeButton={false}
        >
          {engine.label}
        </Button>
      ))}
    </div>
  )
}
