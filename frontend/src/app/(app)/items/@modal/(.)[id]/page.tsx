import { ItemActionsMenu } from "@/components/Items/ItemActionsMenu"
import { ItemDescription } from "@/components/Items/ItemDescription"
import { ItemSheet } from "@/components/Items/ItemSheet"
import { loadItem } from "@/lib/dal"
import { formatCreated } from "@/lib/utils"

// Item details in a modal.
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const item = await loadItem(id)

  return (
    <ItemSheet
      title={item.title}
      description={formatCreated(item.created_at)}
      actions={<ItemActionsMenu item={item} redirectTo="/items" />}
    >
      <ItemDescription description={item.description} />
    </ItemSheet>
  )
}
