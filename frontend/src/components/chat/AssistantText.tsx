"use client"

import { MarkdownText } from "@/components/assistant-ui/elements/markdown-text"
import { SyntaxHighlighter } from "@/components/assistant-ui/elements/shiki-highlighter.aui"

const MARKDOWN_COMPONENTS = {
  SyntaxHighlighter,
  img: () => null,
  a: (props) => (
    <a
      {...props}
      className="text-primary underline underline-offset-4 hover:text-primary/80"
      target="_blank"
      rel="noopener noreferrer"
    />
  ),
} satisfies Parameters<typeof MarkdownText>[0]["components"]

// The assistant's text as markdown, with highlighted code, no images and links in a new tab.
export function AssistantText() {
  return <MarkdownText components={MARKDOWN_COMPONENTS} />
}
