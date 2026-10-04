"use client"

import { useRouter } from "next/navigation"
import { type ReactNode, useState } from "react"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"

// Sheet for item details.
export function ItemSheet({
  title,
  description,
  actions,
  children,
}: {
  title: string
  description?: string
  actions?: ReactNode
  children?: ReactNode
}) {
  const router = useRouter()
  const [open, setOpen] = useState(true)

  return (
    <Sheet
      open={open}
      onOpenChange={setOpen}
      onOpenChangeComplete={(isOpen) => {
        if (!isOpen) router.back()
      }}
    >
      <SheetContent>
        <SheetHeader className="flex-row items-start justify-between gap-2 pr-14">
          <div className="flex min-w-0 flex-col gap-0.5">
            <SheetTitle>{title}</SheetTitle>
            {description && <SheetDescription>{description}</SheetDescription>}
          </div>
          {actions}
        </SheetHeader>
        {children && <div className="px-4">{children}</div>}
      </SheetContent>
    </Sheet>
  )
}
