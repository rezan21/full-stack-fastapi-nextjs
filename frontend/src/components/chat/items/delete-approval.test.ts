import { describe, expect, test } from "bun:test"
import { deleteApprovalDisplay } from "@/components/chat/items/delete-approval"

describe("deleteApprovalDisplay", () => {
  const deleted = (message: string) =>
    JSON.stringify({ changed: true, message, item: null })

  test("asks while the gate is open", () => {
    expect(deleteApprovalDisplay({ approved: undefined }, undefined)).toEqual({
      state: "request",
    })
  })

  test("shows the approved delete as running until the result arrives", () => {
    expect(deleteApprovalDisplay({ approved: true }, undefined)).toEqual({
      state: "running",
    })
  })

  test("shows the deletion once the result arrives", () => {
    expect(
      deleteApprovalDisplay({ approved: true }, deleted("Deleted “Milk”.")),
    ).toEqual({ state: "done", statusLabel: "Deleted “Milk”." })
  })

  test("shows a declined delete as kept", () => {
    expect(deleteApprovalDisplay({ approved: false }, undefined)).toEqual({
      state: "denied",
      statusLabel: "Kept",
    })
  })

  test("shows a request nobody answered as denied with nothing deleted", () => {
    expect(
      deleteApprovalDisplay({ resolution: "cancelled" }, undefined),
    ).toEqual({ state: "denied", statusLabel: "No answer, nothing deleted" })
  })

  test("shows an item that was not found without asking", () => {
    const result = JSON.stringify({
      changed: false,
      message: "You have no item with that id.",
      item: null,
    })

    expect(deleteApprovalDisplay(undefined, result)).toEqual({
      state: "done",
      statusLabel: "You have no item with that id.",
    })
  })
})
