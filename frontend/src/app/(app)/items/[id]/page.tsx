import { ArrowLeft } from "lucide-react"
import type { Metadata } from "next"
import Link from "next/link"
import { PageHeader } from "@/components/Common/PageHeader"
import { ItemActionsMenu } from "@/components/Items/ItemActionsMenu"
import { ItemDescription } from "@/components/Items/ItemDescription"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { loadItem } from "@/lib/dal"
import { formatCreated } from "@/lib/utils"

export const metadata: Metadata = { title: "Item - FastAPI Template" }

// Item details page.
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const item = await loadItem(id)

  return (
    <div className="flex flex-col gap-6">
      <Button
        variant="ghost"
        size="sm"
        className="self-start"
        nativeButton={false}
        render={<Link href="/items" />}
      >
        <ArrowLeft data-icon="inline-start" />
        Back to items
      </Button>

      <PageHeader
        title={item.title}
        description={formatCreated(item.created_at)}
      >
        <ItemActionsMenu item={item} redirectTo="/items" />
      </PageHeader>

      <Card>
        <CardHeader>
          <CardTitle>Description</CardTitle>
        </CardHeader>
        <CardContent>
          <ItemDescription description={item.description} />
        </CardContent>
      </Card>
    </div>
  )
}
