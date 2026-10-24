import { ToolCallStatus } from "@copilotkit/react-core/v2"
import {
  useFrontendTool,
  useRenderTool,
} from "@copilotkit/react-core/v2/headless"
import { z } from "zod"
import { FlyToToolNote } from "@/components/chat/FlyToToolNote"
import { ItemsToolCard } from "@/components/chat/ItemsToolCard"
import { LIST_ITEMS_TOOL } from "@/lib/items-tool"
import { FLY_TO_TOOL, flyTo, type Place, placeSchema } from "@/lib/place"

const noParameters = z.object({})

// Registers the assistant's tools with CopilotKit: how a tool call looks, and what runs in the browser.
export function CopilotKitTools({
  onFlyTo,
}: {
  onFlyTo: (place: Place) => void
}) {
  useFrontendTool(
    {
      name: FLY_TO_TOOL,
      description: "Move the map the user is looking at to a place.",
      parameters: placeSchema,
      handler: async (args) => flyTo(args, onFlyTo),
      render: ({ status, args }) => (
        <FlyToToolNote
          isDone={status === ToolCallStatus.Complete}
          place={args}
        />
      ),
    },
    [onFlyTo],
  )
  useRenderTool({
    name: LIST_ITEMS_TOOL,
    parameters: noParameters,
    render: ({ status, result }) => (
      <ItemsToolCard
        isDone={status === ToolCallStatus.Complete}
        result={result}
      />
    ),
  })
  return null
}
