import { cn } from "@/lib/utils"

export function ItemDescription({
  description,
}: {
  description?: string | null
}) {
  return (
    <p className={cn(!description && "italic text-muted-foreground")}>
      {description || "No description"}
    </p>
  )
}
