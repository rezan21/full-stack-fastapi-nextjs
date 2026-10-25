import { describe, expect, test } from "bun:test"
import { createElement } from "react"
import { renderToStaticMarkup } from "react-dom/server"
import { ElicitationForm } from "@/components/assistant-ui/elements/elicitation-form"
import {
  formDefaults,
  formFields,
  formPayload,
} from "@/components/chat/interrupt-form"

const contract = await Bun.file(
  new URL("../../../../backend/openapi.json", import.meta.url),
).json()
const ITEM_CREATE = contract.components.schemas.ItemCreate

const ITEM_FORM = {
  type: "object",
  required: ["title"],
  properties: {
    title: { type: "string", title: "Title", default: "Milk" },
    description: {
      title: "Description",
      default: null,
      anyOf: [{ type: "string" }, { type: "null" }],
    },
  },
}

const MIXED_FORM = {
  properties: {
    size: { type: "string", enum: ["small", "large"] },
    gift: { type: "boolean" },
    wrap: { anyOf: [{ type: "boolean" }, { type: "null" }], default: true },
  },
}

describe("formDefaults", () => {
  test("starts from the defaults the schema carries", () => {
    expect(formDefaults(ITEM_FORM)).toEqual({ title: "Milk", description: "" })
  })

  test("starts a toggle off unless the schema turns it on", () => {
    expect(formDefaults(MIXED_FORM)).toEqual({
      size: "",
      gift: "false",
      wrap: "true",
    })
  })

  test("starts empty for a missing schema", () => {
    expect(formDefaults(undefined)).toEqual({})
  })
})

describe("formFields", () => {
  test("draws a text field for each string property and marks the required ones", () => {
    const fields = formFields(ITEM_FORM, { title: "Milk", description: "" })

    expect(fields).toEqual([
      {
        name: "title",
        label: "Title",
        value: "Milk",
        kind: "text",
        options: undefined,
        required: true,
      },
      {
        name: "description",
        label: "Description",
        value: "",
        kind: "text",
        options: undefined,
        required: false,
      },
    ])
  })

  test("draws a choice from an enum and a toggle from a boolean, even a nullable one", () => {
    const kinds = formFields(MIXED_FORM, {}).map((f) => [f.name, f.kind])

    expect(kinds).toEqual([
      ["size", "choice"],
      ["gift", "toggle"],
      ["wrap", "toggle"],
    ])
    expect(formFields(MIXED_FORM, {})[0].options).toEqual(["small", "large"])
  })

  test("labels a property by its name when the schema gives no title", () => {
    expect(formFields(MIXED_FORM, {})[0].label).toBe("size")
  })

  test("draws nothing for a schema that is not an object schema", () => {
    expect(formFields(undefined, {})).toEqual([])
    expect(formFields({ properties: "no" }, {})).toEqual([])
  })
})

describe("formPayload", () => {
  test("keeps text as typed and turns a toggle into a boolean", () => {
    const values = { size: "large", gift: "true", wrap: "false" }

    expect(formPayload(MIXED_FORM, values)).toEqual({
      size: "large",
      gift: true,
      wrap: false,
    })
  })

  test("answers an unfilled text field with empty text", () => {
    expect(formPayload(ITEM_FORM, { title: "Milk" })).toEqual({
      title: "Milk",
      description: "",
    })
  })
})

describe("the form the contract describes for a new item", () => {
  test("asks for a required title and an optional description as text", () => {
    const fields = formFields(ITEM_CREATE, formDefaults(ITEM_CREATE))

    expect(
      Object.fromEntries(fields.map((f) => [f.name, [f.kind, f.required]])),
    ).toEqual({ title: ["text", true], description: ["text", false] })
  })

  test("is drawn with its fields, and cannot be sent until the title is filled in", () => {
    const draw = (title: string) =>
      renderToStaticMarkup(
        createElement(ElicitationForm, {
          server: "Assistant",
          message: "Add an item",
          state: "request",
          fields: formFields(ITEM_CREATE, { title, description: "" }),
          onFieldChange: () => {},
        }),
      )

    expect(draw("")).toContain("Title")
    expect(draw("")).toContain("Description")
    expect(draw("")).toMatch(/<button[^>]*\sdisabled=""[^>]*>Send/)
    expect(draw("Milk")).not.toMatch(/<button[^>]*\sdisabled=""[^>]*>Send/)
  })
})
