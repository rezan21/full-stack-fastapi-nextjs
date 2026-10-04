import type { ReactNode } from "react"
import { Document } from "@/components/common/Document"
import { Providers } from "@/components/providers/Providers"
import { siteMetadata } from "@/lib/site-metadata"

export const metadata = siteMetadata

// Root layout of the pages that are the same for everyone, so a CDN can cache them.
export default function Layout({ children }: { children: ReactNode }) {
  return (
    <Document>
      <Providers>{children}</Providers>
    </Document>
  )
}
