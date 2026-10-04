export type ItemColumnId = "id" | "title" | "description" | "actions"

export type ItemColumn = {
  id: ItemColumnId
  header: string
  srOnlyHeader?: boolean
  skeletonClassName: string
  alignEnd?: boolean
}

export const ITEM_COLUMNS: ItemColumn[] = [
  { id: "id", header: "ID", skeletonClassName: "h-4 w-64" },
  { id: "title", header: "Title", skeletonClassName: "h-4 w-32" },
  { id: "description", header: "Description", skeletonClassName: "h-4 w-48" },
  {
    id: "actions",
    header: "Actions",
    srOnlyHeader: true,
    skeletonClassName: "size-8 rounded-md",
    alignEnd: true,
  },
]
