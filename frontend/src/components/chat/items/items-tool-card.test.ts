import { describe, expect, test } from "bun:test"
import type { ToolCallMessagePartStatus } from "@assistant-ui/react"
import { createElement } from "react"
import { renderToStaticMarkup } from "react-dom/server"
import { ItemsToolCard } from "@/components/chat/items/ItemsToolCard"

const CHECK = "lucide-check"
const WARNING = "text-destructive"

const ITEM = { id: "c2b9c6a4", title: "Milk", description: "2 litres" }

const draw = (status: ToolCallMessagePartStatus, result?: unknown) =>
  renderToStaticMarkup(
    createElement(ItemsToolCard, { status, argsText: "{}", result }),
  )

describe("ItemsToolCard", () => {
  test("shows the lookup as a running tool call before there is a result", () => {
    const html = draw({ type: "running" })

    expect(html).toContain('data-slot="tool-call"')
    expect(html).not.toContain(CHECK)
    expect(html).not.toContain("Milk")
  })

  test("shows the lookup as a finished tool call above the items it found", () => {
    const html = draw(
      { type: "complete" },
      JSON.stringify({ count: 1, data: [ITEM] }),
    )

    expect(html.indexOf('data-slot="tool-call"')).toBeGreaterThan(-1)
    expect(html.indexOf('data-slot="tool-call"')).toBeLessThan(
      html.indexOf("Milk"),
    )
    expect(html).toContain("2 litres")
    expect(html).toContain(CHECK)
  })

  test("counts the items it found", () => {
    const html = draw(
      { type: "complete" },
      JSON.stringify({ count: 2, data: [ITEM, { ...ITEM, id: "d3" }] }),
    )

    expect(html).toContain("2 items")
  })

  test("says there are no items when the lookup found none", () => {
    const html = draw(
      { type: "complete" },
      JSON.stringify({ count: 0, data: [] }),
    )

    expect(html).toContain("You have no items yet")
    expect(html).toContain(CHECK)
  })

  test("says the items could not be shown for a result it cannot read, without a check", () => {
    const html = draw({ type: "complete" }, "not json")

    expect(html).toContain("Your items could not be shown.")
    expect(html).toContain(WARNING)
    expect(html).not.toContain(CHECK)
    expect(html).not.toContain('data-slot="tool-call"')
  })

  test("says a lookup that did not finish, without a check", () => {
    const html = draw({ type: "incomplete", reason: "cancelled" })

    expect(html).toContain("Looking up your items (didn&#x27;t finish)")
    expect(html).not.toContain(CHECK)
  })
})
