import type { ReactNode } from "react"
import { Document } from "@/components/common/Document"
import { NoncedProviders } from "@/components/providers/NoncedProviders"
import { siteMetadata } from "@/lib/site-metadata"

export const metadata = siteMetadata

// Root layout of the pages rendered per request, which carry a Content-Security-Policy nonce.
export default function Layout({ children }: { children: ReactNode }) {
  return (
    <Document>
      <NoncedProviders>{children}</NoncedProviders>
    </Document>
  )
}
