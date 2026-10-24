import { describe, expect, test } from "bun:test"
import { pageCount, pageHref, pageQuery, parsePage } from "@/lib/pagination"

describe("parsePage", () => {
  test("reads a page number", () => {
    expect(parsePage("3")).toBe(3)
    expect(parsePage(["4", "5"])).toBe(4)
  })

  test("falls back to the first page for anything else", () => {
    for (const value of [undefined, "", "0", "-2", "2.5", "abc", "NaN"]) {
      expect(parsePage(value)).toBe(1)
    }
  })

  test("caps a huge page so the request stays valid", () => {
    expect(parsePage("1e308")).toBe(100_000)
    expect(parsePage("99999999999999999999")).toBe(100_000)
  })
})

describe("pageCount", () => {
  test("is at least one", () => {
    expect(pageCount(0, 20)).toBe(1)
  })

  test("rounds up", () => {
    expect(pageCount(20, 20)).toBe(1)
    expect(pageCount(21, 20)).toBe(2)
    expect(pageCount(200, 20)).toBe(10)
  })
})

describe("pageQuery", () => {
  test("skips the pages before and limits to one page", () => {
    expect(pageQuery(1, 20)).toEqual({ skip: 0, limit: 20 })
    expect(pageQuery(3, 20)).toEqual({ skip: 40, limit: 20 })
  })
})

describe("pageHref", () => {
  test("leaves the first page without a query", () => {
    expect(pageHref("/items", 1)).toBe("/items")
    expect(pageHref("/chat", 1)).toBe("/chat")
  })

  test("links later pages with a page query", () => {
    expect(pageHref("/items", 4)).toBe("/items?page=4")
    expect(pageHref("/chat", 2)).toBe("/chat?page=2")
  })
})
