import { ItemSheet } from "@/components/items/ItemSheet"

// Shown when an item can't be found.
export default function NotFound() {
  return (
    <ItemSheet
      title="Item not found"
      description="It may have been deleted, or it isn't yours."
    />
  )
}
