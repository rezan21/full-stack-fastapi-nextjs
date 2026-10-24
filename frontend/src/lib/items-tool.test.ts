import { describe, expect, test } from "bun:test"
import { parseItemsResult } from "@/lib/items-tool"

describe("parseItemsResult", () => {
  test("reads the items the tool found", () => {
    const result = JSON.stringify({
      count: 1,
      items: [{ id: "i-1", title: "A title", description: null }],
    })

    expect(parseItemsResult(result)).toEqual({
      count: 1,
      items: [{ id: "i-1", title: "A title", description: null }],
    })
  })

  test("reads items a library already parsed", () => {
    const items = [{ id: "i-1", title: "A title", description: "More" }]

    expect(parseItemsResult({ count: 1, items })).toEqual({ count: 1, items })
  })

  test("has nothing to show before there is a result", () => {
    expect(parseItemsResult(undefined)).toBeUndefined()
    expect(parseItemsResult("")).toBeUndefined()
  })

  test("has nothing to show for a result that is not the expected shape", () => {
    expect(parseItemsResult("not json")).toBeUndefined()
    expect(parseItemsResult('{"count":"many","items":[]}')).toBeUndefined()
    expect(parseItemsResult('{"count":1}')).toBeUndefined()
  })
})
