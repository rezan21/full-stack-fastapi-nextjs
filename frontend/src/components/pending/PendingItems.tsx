import { ItemsTableHeader } from "@/components/items/ItemsTableHeader"
import { ITEM_COLUMNS } from "@/components/items/item-columns"
import { Skeleton } from "@/components/ui/skeleton"
import { Table, TableBody, TableCell, TableRow } from "@/components/ui/table"

// Loading placeholder for the items table.
export function PendingItems() {
  return (
    <Table>
      <ItemsTableHeader />
      <TableBody>
        {Array.from({ length: 5 }).map((_, index) => (
          <TableRow key={index}>
            {ITEM_COLUMNS.map((column) => (
              <TableCell key={column.id}>
                <div
                  className={column.alignEnd ? "flex justify-end" : undefined}
                >
                  <Skeleton className={column.skeletonClassName} />
                </div>
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
