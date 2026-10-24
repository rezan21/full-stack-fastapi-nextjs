import { describe, expect, test } from "bun:test"
import {
  itemFormDefaults,
  parseItemChange,
  parseItemsResult,
} from "@/lib/items-tool"

const ITEM = {
  id: "c2b9c6a4-8f5e-4d4a-9a4e-1f2b3c4d5e6f",
  title: "Milk",
  description: null,
}

describe("parseItemsResult", () => {
  test("reads the items the tool found", () => {
    const result = JSON.stringify({ count: 1, data: [ITEM] })

    expect(parseItemsResult(result)).toEqual({ count: 1, data: [ITEM] })
  })

  test("has nothing to show before there is a result", () => {
    expect(parseItemsResult(undefined)).toBeUndefined()
    expect(parseItemsResult("")).toBeUndefined()
  })

  test("has nothing to show for a result that is not the expected shape", () => {
    expect(parseItemsResult("not json")).toBeUndefined()
    expect(parseItemsResult('{"count":"many","data":[]}')).toBeUndefined()
    expect(parseItemsResult('{"count":1}')).toBeUndefined()
  })
})

describe("parseItemChange", () => {
  test("reads what a change did and the item it changed", () => {
    const result = JSON.stringify({
      changed: true,
      message: "Added “Milk”.",
      item: ITEM,
    })

    expect(parseItemChange(result)).toEqual({
      changed: true,
      message: "Added “Milk”.",
      item: ITEM,
    })
  })

  test("reads a change that did nothing, which has no item", () => {
    const result = JSON.stringify({
      changed: false,
      message: "Cancelled. Nothing was added.",
      item: null,
    })

    expect(parseItemChange(result)?.message).toBe(
      "Cancelled. Nothing was added.",
    )
  })

  test("has nothing to say before there is a result", () => {
    expect(parseItemChange(undefined)).toBeUndefined()
  })
})

describe("itemFormDefaults", () => {
  test("starts the form with the title and description the assistant was given", () => {
    const schema = {
      properties: {
        title: { default: "test" },
        description: { default: "testing" },
      },
    }

    expect(itemFormDefaults(schema)).toEqual({
      title: "test",
      description: "testing",
    })
  })

  test("keeps the title when the description has no default", () => {
    const schema = {
      properties: {
        title: { default: "Milk" },
        description: { default: null },
      },
    }

    expect(itemFormDefaults(schema)).toEqual({ title: "Milk", description: "" })
  })

  test("starts the form empty when the assistant gave nothing", () => {
    const schema = { properties: { title: {}, description: {} } }

    expect(itemFormDefaults(schema)).toEqual({ title: "", description: "" })
    expect(itemFormDefaults(undefined)).toEqual({ title: "", description: "" })
  })
})
