import { MessageSquare } from "lucide-react"
import type { Metadata } from "next"
import { ConversationList } from "@/components/chat/ConversationList"
import { NewChatButton } from "@/components/chat/NewChatButton"
import { PageHeader } from "@/components/common/PageHeader"
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty"
import { getConversations } from "@/lib/api"

export const metadata: Metadata = { title: "AI Chat - FastAPI Template" }

// AI chat page.
export default async function Page() {
  const conversations = await getConversations()

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
        <ConversationList conversations={conversations.data} />
      )}
    </div>
  )
}
