"use client"

import { CSPProvider } from "@base-ui/react/csp-provider"
import type { ReactNode } from "react"
import { ThemeProvider } from "@/components/providers/ThemeProvider"
import { Toaster } from "@/components/ui/sonner"
import { TooltipProvider } from "@/components/ui/tooltip"

// Providers every page needs, with the nonce of a page that has one.
export function Providers({
  nonce,
  children,
}: {
  nonce?: string
  children: ReactNode
}) {
  return (
    <CSPProvider nonce={nonce}>
      <ThemeProvider
        nonce={nonce}
        attribute="class"
        defaultTheme="dark"
        enableSystem
        disableTransitionOnChange
      >
        <TooltipProvider>{children}</TooltipProvider>
        <Toaster richColors closeButton />
      </ThemeProvider>
    </CSPProvider>
  )
}
