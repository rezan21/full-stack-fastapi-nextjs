import Link from "next/link"
import type { ReactNode } from "react"

// Confirmation shown after an emailed link is requested.
export function CheckEmail({ children }: { children: ReactNode }) {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-2xl font-bold tracking-tight">Check your email</h1>
        <p className="text-sm text-muted-foreground">{children}</p>
      </div>

      <div className="text-center text-sm">
        <Link href="/login" className="underline underline-offset-4">
          Back to log in
        </Link>
      </div>
    </div>
  )
}
