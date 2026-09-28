import { ITEM_COLUMNS } from "@/components/Items/item-columns"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

const PendingItems = () => (
  <Table>
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
    <TableBody>
      {Array.from({ length: 5 }).map((_, index) => (
        <TableRow key={index}>
          {ITEM_COLUMNS.map((column) => (
            <TableCell key={column.id}>
              <div className={column.alignEnd ? "flex justify-end" : undefined}>
                <Skeleton className={column.skeletonClassName} />
              </div>
            </TableCell>
          ))}
        </TableRow>
      ))}
    </TableBody>
  </Table>
)

export default PendingItems
