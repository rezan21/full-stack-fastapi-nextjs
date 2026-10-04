import { redirect } from "next/navigation"
import type { ReactNode } from "react"
import { Footer } from "@/components/common/Footer"
import { AppSidebar } from "@/components/sidebar/AppSidebar"
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import { getUser } from "@/lib/dal"

// Layout for the main app pages.
export default async function Layout({ children }: { children: ReactNode }) {
  const user = await getUser()
  if (!user) redirect("/login")

  return (
    <SidebarProvider>
      <AppSidebar user={user} />
      <SidebarInset>
        <header className="sticky top-0 z-10 flex h-16 shrink-0 items-center gap-2 border-b bg-background px-4">
          <SidebarTrigger className="-ml-1" />
        </header>
        <main className="flex-1 p-6 md:p-8">
          <div className="mx-auto max-w-7xl">{children}</div>
        </main>
        <Footer />
      </SidebarInset>
    </SidebarProvider>
  )
}
