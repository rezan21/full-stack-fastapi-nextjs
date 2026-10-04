import { CSPProvider } from "@base-ui/react/csp-provider"
import type { Metadata } from "next"
import { Geist } from "next/font/google"
import { headers } from "next/headers"
import type { ReactNode } from "react"
import { ThemeProvider } from "@/components/providers/ThemeProvider"
import { Toaster } from "@/components/ui/sonner"
import { TooltipProvider } from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"
import "./globals.css"

const geist = Geist({ subsets: ["latin"], variable: "--font-sans" })

export const metadata: Metadata = {
  title: "FastAPI Template",
  description: "Full Stack FastAPI Template",
  icons: { icon: "/assets/images/favicon.png" },
}

// Root layout for every page.
export default async function RootLayout({
  children,
}: {
  children: ReactNode
}) {
  const nonce = (await headers()).get("x-nonce") ?? undefined
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={cn("font-sans", geist.variable)}>
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
      </body>
    </html>
  )
}
