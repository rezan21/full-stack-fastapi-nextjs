import { Geist } from "next/font/google"
import type { ReactNode } from "react"
import { cn } from "@/lib/utils"
import "@/app/globals.css"

const geist = Geist({ subsets: ["latin"], variable: "--font-sans" })

// The HTML document every root layout renders.
export function Document({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={cn("font-sans", geist.variable)}>{children}</body>
    </html>
  )
}
