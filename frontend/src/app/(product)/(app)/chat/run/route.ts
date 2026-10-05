import { proxyChatRun } from "@/lib/chat-proxy"

// Streams the assistant's reply to a chat message.
export function POST(request: Request) {
  return proxyChatRun(request)
}
