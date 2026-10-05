import type { Metadata } from "next"
import Link from "next/link"
import { ChatView } from "@/components/chat/ChatView"
import { NewChatButton } from "@/components/chat/NewChatButton"
import { PageHeader } from "@/components/common/PageHeader"
import { Button } from "@/components/ui/button"
import { loadConversation, loadMessages } from "@/lib/dal"

export const metadata: Metadata = { title: "AI Chat - FastAPI Template" }

// Conversation page.
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const conversation = await loadConversation(id)
  const history = await loadMessages(id)

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title={conversation.title ?? "New chat"}
        description="AI Chat"
      >
        <div className="flex gap-2">
          <Button
            variant="outline"
            render={<Link href="/chat" />}
            nativeButton={false}
          >
            All chats
          </Button>
          <NewChatButton />
        </div>
      </PageHeader>

      <ChatView
        key={id}
        conversationId={id}
        history={history.data}
        total={history.count}
      />
    </div>
  )
}
