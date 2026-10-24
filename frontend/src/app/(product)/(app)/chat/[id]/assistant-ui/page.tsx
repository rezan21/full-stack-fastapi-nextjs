import type { Metadata } from "next"
import { AssistantUiChat } from "@/components/chat/assistant-ui/AssistantUiChat"
import { EngineSwitcher } from "@/components/chat/EngineSwitcher"
import { PageHeader } from "@/components/common/PageHeader"
import { loadConversation, loadMessages } from "@/lib/dal"

export const metadata: Metadata = {
  title: "AI Chat (assistant-ui) - FastAPI Template",
}

// Conversation page run through assistant-ui.
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
        description="AI Chat · assistant-ui"
      >
        <EngineSwitcher conversationId={id} current="/assistant-ui" />
      </PageHeader>

      <AssistantUiChat
        key={id}
        conversationId={id}
        history={history.data}
        total={history.count}
      />
    </div>
  )
}
