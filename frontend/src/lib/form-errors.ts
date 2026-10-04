import type { z } from "zod"

const FIELD_NAMES: Record<string, string> = { username: "email" }

// Turns a schema path into a field label.
function fieldLabel(path: PropertyKey[] | undefined): string {
  const key = String(path?.at(-1) ?? "field")
  const name = FIELD_NAMES[key] ?? key.replaceAll("_", " ")
  return name.charAt(0).toUpperCase() + name.slice(1)
}

// Maps validation issues to messages.
export const formError: z.core.$ZodErrorMap = (issue) => {
  const field = fieldLabel(issue.path)
  if (issue.code === "too_small" && issue.origin === "string") {
    return issue.input === ""
      ? `${field} is required`
      : `${field} must be at least ${issue.minimum} characters`
  }
  if (issue.code === "too_big" && issue.origin === "string") {
    return `${field} must be at most ${issue.maximum} characters`
  }
  if (issue.code === "invalid_format" && issue.format === "regex") {
    return `Invalid ${field.toLowerCase()}`
  }
}
