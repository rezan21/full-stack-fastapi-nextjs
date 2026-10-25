import { describe, expect, test } from "bun:test"
import type { ToolCallMessagePartStatus } from "@assistant-ui/react"
import { createElement } from "react"
import { renderToStaticMarkup } from "react-dom/server"
import { ToolNote } from "@/components/chat/ToolNote"

const CHECK = "lucide-check"
const WARNING = "text-destructive"

const draw = (
  status: ToolCallMessagePartStatus,
  props: { query?: string; failure?: string } = {},
) =>
  renderToStaticMarkup(
    createElement(ToolNote, {
      status,
      running: "Adding an item",
      done: "Added an item",
      request: '{"title":"Milk"}',
      result: "Added “Milk”.",
      ...props,
    }),
  )

const shownLabel = (html: string) =>
  html.match(/aria-hidden="false"[^>]*>(?:<[^>]+>)*([^<]+)/)?.[1]

describe("ToolNote", () => {
  test("says what the assistant is doing while the call runs", () => {
    const html = draw({ type: "running" })

    expect(shownLabel(html)).toBe("Adding an item")
    expect(html).not.toContain(CHECK)
  })

  test("says what the assistant did, with its target, once the call completes", () => {
    const html = draw({ type: "complete" }, { query: "Milk" })

    expect(shownLabel(html)).toBe("Added an item")
    expect(html).toContain("Milk")
    expect(html).toContain(CHECK)
  })

  test("marks a target that is not known yet", () => {
    expect(draw({ type: "running" })).toContain("…")
  })

  test("keeps the request and result closed until asked for", () => {
    const html = draw({ type: "complete" })

    expect(html).not.toContain("Request")
    expect(html).not.toContain("Added “Milk”.")
  })

  test("says a call that did not finish, without a check", () => {
    const html = draw({ type: "incomplete", reason: "cancelled" })

    expect(html).toContain("Adding an item (didn&#x27;t finish)")
    expect(html).toContain(WARNING)
    expect(html).not.toContain(CHECK)
  })

  test("says why a finished call did nothing, without a check", () => {
    const html = draw(
      { type: "complete" },
      { failure: "Cancelled. Nothing was added." },
    )

    expect(html).toContain("Cancelled. Nothing was added.")
    expect(html).toContain(WARNING)
    expect(html).not.toContain("Added an item")
    expect(html).not.toContain(CHECK)
  })
})
