export { cn } from "cn"

export function getInitials(name: string): string {
  return name
    .split(" ")
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase()
}

export function formatCreated(createdAt?: string | null): string | undefined {
  if (!createdAt) return undefined
  const date = new Date(createdAt).toLocaleDateString("en-US", {
    dateStyle: "long",
    timeZone: "UTC",
  })
  return `Created ${date}`
}
