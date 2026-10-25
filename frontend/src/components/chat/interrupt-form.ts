import { z } from "zod"
import type { ElicitationField } from "@/components/assistant-ui/elements/elicitation-form"

export type FormValues = Record<string, string>

const propertySchema = z.object({
  title: z.string().optional(),
  type: z.union([z.string(), z.array(z.string())]).optional(),
  anyOf: z.array(z.object({ type: z.string().optional() })).optional(),
  enum: z.array(z.string()).optional(),
  default: z.unknown().optional(),
})

const formSchema = z.object({
  properties: z.record(z.string(), propertySchema).default({}),
  required: z.array(z.string()).default([]),
})

type Property = z.infer<typeof propertySchema>

// Reads the form a JSON Schema describes, which is no form when it is missing or not an object schema.
function readForm(schema: Record<string, unknown> | undefined) {
  const form = formSchema.safeParse(schema ?? {})
  return form.success ? form.data : { properties: {}, required: [] }
}

// Returns which kind of field a property is drawn as.
function kindOf(property: Property): ElicitationField["kind"] {
  if (property.enum) return "choice"
  const types = [property.type, ...(property.anyOf ?? []).map((o) => o.type)]
  return types.flat().includes("boolean") ? "toggle" : "text"
}

// Returns the values a form starts with, taken from the schema's defaults.
export function formDefaults(
  schema: Record<string, unknown> | undefined,
): FormValues {
  const { properties } = readForm(schema)
  return Object.fromEntries(
    Object.entries(properties).map(([name, property]) => {
      const value = property.default
      if (typeof value === "string") return [name, value]
      if (typeof value === "boolean") return [name, String(value)]
      return [name, kindOf(property) === "toggle" ? "false" : ""]
    }),
  )
}

// Returns the fields a schema asks for, holding the given values.
export function formFields(
  schema: Record<string, unknown> | undefined,
  values: FormValues,
): ElicitationField[] {
  const { properties, required } = readForm(schema)
  return Object.entries(properties).map(([name, property]) => ({
    name,
    label: property.title ?? name,
    value: values[name] ?? "",
    kind: kindOf(property),
    options: property.enum,
    required: required.includes(name),
  }))
}

// Returns the answer the values make, with each value in the type its property has.
export function formPayload(
  schema: Record<string, unknown> | undefined,
  values: FormValues,
): Record<string, string | boolean> {
  const { properties } = readForm(schema)
  return Object.fromEntries(
    Object.entries(properties).map(([name, property]) => [
      name,
      kindOf(property) === "toggle"
        ? values[name] === "true"
        : (values[name] ?? ""),
    ]),
  )
}
