import type { Metadata } from "next"
import { CopilotKitChat } from "@/components/chat/copilotkit/CopilotKitChat"
import { EngineSwitcher } from "@/components/chat/EngineSwitcher"
import { PageHeader } from "@/components/common/PageHeader"
import { loadConversation, loadMessages } from "@/lib/dal"

export const metadata: Metadata = {
  title: "AI Chat (CopilotKit) - FastAPI Template",
}

// Conversation page run through CopilotKit.
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
        description="AI Chat · CopilotKit"
      >
        <EngineSwitcher conversationId={id} current="/copilotkit" />
      </PageHeader>

      <CopilotKitChat
        key={id}
        conversationId={id}
        history={history.data}
        total={history.count}
      />
    </div>
  )
}
