import { defineToolkit } from "@assistant-ui/react"
import {
  CREATE_ITEM_TOOL,
  DELETE_ITEM_TOOL,
  LIST_ITEMS_TOOL,
  UPDATE_ITEM_TOOL,
} from "@/lib/items-tool"
import { DeleteItemToolCard } from "./DeleteItemToolCard"
import { ItemChangeToolNote } from "./ItemChangeToolNote"
import { ItemsToolCard } from "./ItemsToolCard"

// The item tools the server runs, drawn in the chat.
export const itemsToolkit = defineToolkit({
  [LIST_ITEMS_TOOL]: { type: "backend", render: ItemsToolCard },
  [CREATE_ITEM_TOOL]: { type: "backend", render: ItemChangeToolNote },
  [UPDATE_ITEM_TOOL]: { type: "backend", render: ItemChangeToolNote },
  [DELETE_ITEM_TOOL]: {
    type: "backend",
    display: "standalone",
    render: DeleteItemToolCard,
  },
})
