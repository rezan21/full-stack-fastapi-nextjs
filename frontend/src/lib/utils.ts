export { cn } from "cn"

// Returns the initials for a name.
export function getInitials(name: string): string {
  return name
    .split(" ")
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase()
}

// Formats a creation date as a label.
export function formatCreated(createdAt?: string | null): string | undefined {
  if (!createdAt) return undefined
  const date = new Date(createdAt).toLocaleDateString("en-US", {
    dateStyle: "long",
    timeZone: "UTC",
  })
  return `Created ${date}`
}
