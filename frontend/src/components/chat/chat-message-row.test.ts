import { describe, expect, test } from "bun:test"
import {
  AssistantRuntimeProvider,
  type ThreadMessageLike,
  ThreadPrimitive,
  useExternalStoreRuntime,
} from "@assistant-ui/react"
import { createElement } from "react"
import { renderToStaticMarkup } from "react-dom/server"
import { ChatMessageRow } from "@/components/chat/ChatMessageRow"

const COMPLETE = { type: "complete", reason: "stop" } as const
const RUNNING = { type: "running" } as const

function Harness({ messages }: { messages: ThreadMessageLike[] }) {
  const runtime = useExternalStoreRuntime<ThreadMessageLike>({
    messages,
    convertMessage: (message) => message,
    onNew: async () => {},
  })
  return createElement(
    AssistantRuntimeProvider,
    { runtime },
    createElement(
      ThreadPrimitive.Root,
      null,
      createElement(
        ThreadPrimitive.Viewport,
        null,
        createElement(ThreadPrimitive.Messages, {
          // biome-ignore lint/correctness/noChildrenProp: the thread's children is a render function, which createElement's children cannot type
          children: () => createElement(ChatMessageRow),
        }),
      ),
    ),
  )
}

const draw = (...messages: ThreadMessageLike[]) =>
  renderToStaticMarkup(createElement(Harness, { messages }))

const user = (text: string): ThreadMessageLike => ({
  id: "u1",
  role: "user",
  content: [{ type: "text", text }],
})

const assistant = (
  content: ThreadMessageLike["content"],
  status: ThreadMessageLike["status"] = COMPLETE,
): ThreadMessageLike => ({ id: "a1", role: "assistant", content, status })

describe("ChatMessageRow", () => {
  test("is the message root the thread viewport finds its messages by", () => {
    const html = draw(user("Hi there"))

    expect(html).toContain('data-slot="message"')
    expect(html).toContain('data-message-id="u1"')
  })

  test("offers to copy a user's message, shown while it is hovered or focused", () => {
    const html = draw(user("Hi there"))

    expect(html).toContain('data-slot="message-footer"')
    expect(html).toContain("opacity-0")
    expect(html).toContain("group-hover/message:opacity-100")
    expect(html).toContain("focus-within:opacity-100")
    expect(html).toContain("pointer-coarse:opacity-100")
  })

  test("offers to copy an assistant's reply the same way", () => {
    const html = draw(user("Hi"), assistant([{ type: "text", text: "Hello!" }]))

    expect(html.match(/data-slot="message-footer"/g)).toHaveLength(2)
  })

  test("offers no copy under a reply that is only a tool call", () => {
    const html = draw(
      assistant([
        {
          type: "tool-call",
          toolCallId: "c1",
          toolName: "unknown_tool",
          args: {},
        },
      ]),
    )

    expect(html).toContain("1 tool call")
    expect(html).not.toContain('data-slot="message-footer"')
  })

  test("shows the reasoning of a reply as a disclosure above its text", () => {
    const html = draw(
      assistant([
        { type: "reasoning", text: "Weighing the options" },
        { type: "text", text: "Hello!" },
      ]),
    )

    expect(html).toContain('data-slot="reasoning-trigger"')
    expect(html.indexOf('data-slot="reasoning-trigger"')).toBeLessThan(
      html.indexOf("Hello!"),
    )
  })

  test("holds the reasoning open while it streams, without a separate thinking line", () => {
    const html = draw(
      assistant([{ type: "reasoning", text: "Weighing the options" }], RUNNING),
    )

    expect(html).toContain('aria-expanded="true"')
    expect(html).toContain('aria-busy="true"')
    expect(html).not.toContain('data-slot="thinking-indicator"')
  })

  test("keeps the reasoning closed once the reply is done", () => {
    const html = draw(
      assistant([
        { type: "reasoning", text: "Weighing the options" },
        { type: "text", text: "Hello!" },
      ]),
    )

    expect(html).toContain('aria-expanded="false"')
    expect(html).not.toContain("Weighing the options")
  })

  test("draws no images and opens links in a new tab in what the model wrote", () => {
    const html = draw(
      assistant([
        {
          type: "text",
          text: "See ![pic](https://evil.test/p.png) and [docs](https://example.com)",
        },
      ]),
    )

    expect(html).not.toContain("<img")
    expect(html).toContain('target="_blank"')
    expect(html).toContain('rel="noopener noreferrer"')
  })

  test("shows that the assistant is thinking while its reply has nothing to show yet", () => {
    const html = draw(user("Hi"), assistant([], RUNNING))

    expect(html).toContain('data-slot="thinking-indicator"')
    expect(html).toContain("Thinking")
  })

  test("shows that the assistant is working again once a tool call finished and nothing else came", () => {
    const html = draw(
      assistant(
        [
          {
            type: "tool-call",
            toolCallId: "c1",
            toolName: "unknown_tool",
            args: {},
            result: "ok",
          },
        ],
        RUNNING,
      ),
    )

    expect(html).toContain('data-slot="thinking-indicator"')
  })

  test("does not say thinking while the reply's text is arriving", () => {
    const html = draw(assistant([{ type: "text", text: "Hello" }], RUNNING))

    expect(html).not.toContain('data-slot="thinking-indicator"')
  })

  test("draws nothing for a finished reply with nothing in it", () => {
    expect(draw(assistant([]))).not.toContain('data-slot="message"')
  })
})
