import { describe, expect, test } from "bun:test"
import {
  itemChangeFailure,
  itemProblem,
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

describe("itemChangeFailure", () => {
  test("has no failure for a change that changed the item", () => {
    const change = parseItemChange(
      JSON.stringify({ changed: true, message: "Added “Milk”.", item: ITEM }),
    )

    expect(itemChangeFailure(change)).toBeUndefined()
  })

  test("says why a change did nothing", () => {
    const change = parseItemChange(
      JSON.stringify({
        changed: false,
        message: "Cancelled. Nothing was added.",
        item: null,
      }),
    )

    expect(itemChangeFailure(change)).toBe("Cancelled. Nothing was added.")
  })

  test("says the item could not be changed when the result is not a change", () => {
    expect(itemChangeFailure(parseItemChange("not json"))).toBe(
      "The item could not be changed.",
    )
  })
})

describe("itemProblem", () => {
  test("accepts an item with a title", () => {
    expect(itemProblem({ title: "Milk", description: "" })).toBeUndefined()
  })

  test("says what is wrong with an item that breaks the contract's rules", () => {
    expect(itemProblem({ title: "", description: "" })).toBe(
      "Title is required",
    )
    expect(itemProblem({ title: "x".repeat(256), description: "" })).toBe(
      "Title must be at most 255 characters",
    )
  })
})
