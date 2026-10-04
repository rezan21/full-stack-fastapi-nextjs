import { TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { ITEM_COLUMNS } from "./item-columns"

// Header row of the items table.
export function ItemsTableHeader() {
  return (
    <TableHeader>
      <TableRow>
        {ITEM_COLUMNS.map((column) => (
          <TableHead key={column.id}>
            {column.srOnlyHeader ? (
              <span className="sr-only">{column.header}</span>
            ) : (
              column.header
            )}
          </TableHead>
        ))}
      </TableRow>
    </TableHeader>
  )
}
