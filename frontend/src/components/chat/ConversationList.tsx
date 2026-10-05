import Link from "next/link"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import type { ConversationPublic } from "@/lib/api"
import { formatActivity } from "@/lib/utils"

// Table of a user's conversations.
export function ConversationList({
  conversations,
}: {
  conversations: ConversationPublic[]
}) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Conversation</TableHead>
          <TableHead>Last activity</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {conversations.map((conversation) => (
          <TableRow key={conversation.id}>
            <TableCell>
              <Link
                href={`/chat/${conversation.id}`}
                className="font-medium hover:underline"
              >
                {conversation.title ?? "New chat"}
              </Link>
            </TableCell>
            <TableCell className="text-muted-foreground">
              {formatActivity(conversation.updated_at)}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
