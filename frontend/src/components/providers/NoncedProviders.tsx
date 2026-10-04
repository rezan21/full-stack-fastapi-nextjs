import { headers } from "next/headers"
import type { ReactNode } from "react"
import { Providers } from "@/components/providers/Providers"

// Providers for a page rendered per request, carrying that request's nonce.
export async function NoncedProviders({ children }: { children: ReactNode }) {
  const nonce = (await headers()).get("x-nonce") ?? undefined
  return <Providers nonce={nonce}>{children}</Providers>
}
