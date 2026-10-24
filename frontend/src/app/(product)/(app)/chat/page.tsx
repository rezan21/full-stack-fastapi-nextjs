import { MessageSquare } from "lucide-react"
import type { Metadata } from "next"
import { redirect } from "next/navigation"
import { ConversationList } from "@/components/chat/ConversationList"
import { NewChatButton } from "@/components/chat/NewChatButton"
import { PageHeader } from "@/components/common/PageHeader"
import { PagePagination } from "@/components/common/PagePagination"
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty"
import { getConversations } from "@/lib/api"
import { CONVERSATIONS_PAGE_SIZE } from "@/lib/config"
import { pageCount, pageHref, parsePage } from "@/lib/pagination"

export const metadata: Metadata = { title: "AI Chat - FastAPI Template" }

// AI chat page.
export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ page?: string | string[] }>
}) {
  const page = parsePage((await searchParams).page)
  const conversations = await getConversations(page)
  const pages = pageCount(conversations.count, CONVERSATIONS_PAGE_SIZE)
  if (page > pages) redirect(pageHref("/chat", pages))

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="AI Chat" description="Talk to the assistant">
        <NewChatButton />
      </PageHeader>

      {conversations.count === 0 ? (
        <Empty>
          <EmptyHeader>
            <EmptyMedia variant="icon">
              <MessageSquare />
            </EmptyMedia>
            <EmptyTitle>You don't have any conversations yet</EmptyTitle>
            <EmptyDescription>
              Start a new chat to ask the assistant anything
            </EmptyDescription>
          </EmptyHeader>
          <EmptyContent>
            <NewChatButton />
          </EmptyContent>
        </Empty>
      ) : (
        <>
          <ConversationList conversations={conversations.data} />
          <PagePagination basePath="/chat" page={page} pages={pages} />
        </>
      )}
    </div>
  )
}
