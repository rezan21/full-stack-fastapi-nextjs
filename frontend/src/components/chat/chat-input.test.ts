import { describe, expect, test } from "bun:test"
import {
  AssistantRuntimeProvider,
  type ThreadMessageLike,
  useExternalStoreRuntime,
} from "@assistant-ui/react"
import { createElement } from "react"
import { renderToStaticMarkup } from "react-dom/server"
import { ChatInput } from "@/components/chat/ChatInput"

function Harness({ isRunning }: { isRunning: boolean }) {
  const runtime = useExternalStoreRuntime<ThreadMessageLike>({
    messages: [],
    convertMessage: (message) => message,
    onNew: async () => {},
  })
  return createElement(
    AssistantRuntimeProvider,
    { runtime },
    createElement(ChatInput, {
      isRunning,
      onSend: async () => true,
      onStop: () => {},
    }),
  )
}

const draw = (isRunning: boolean) =>
  renderToStaticMarkup(createElement(Harness, { isRunning }))

describe("ChatInput", () => {
  test("is a form with a message box the user can name", () => {
    const html = draw(false)

    expect(html).toContain("<form")
    expect(html).toMatch(/<textarea[^>]*aria-label="Message"/)
    expect(html).toContain('placeholder="Ask anything"')
  })

  test("cannot send an empty message", () => {
    expect(draw(false)).toMatch(
      /<button[^>]*aria-label="Send"[^>]*disabled=""|<button[^>]*disabled=""[^>]*aria-label="Send"/,
    )
  })

  test("offers to stop, not send, while a reply is running", () => {
    const html = draw(true)

    expect(html).toMatch(/<button[^>]*aria-label="Stop"/)
    expect(html).not.toMatch(/<button[^>]*aria-label="Send"/)
    expect(html).not.toMatch(/<button[^>]*aria-label="Stop"[^>]*disabled=""/)
  })
})
