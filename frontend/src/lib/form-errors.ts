import type { z } from "zod"

function fieldLabel(path: PropertyKey[] | undefined): string {
  const name = String(path?.at(-1) ?? "field").replaceAll("_", " ")
  return name.charAt(0).toUpperCase() + name.slice(1)
}

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
}
