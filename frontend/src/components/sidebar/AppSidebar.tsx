"use client"

import { Blocks, Briefcase, Home } from "lucide-react"
import Link from "next/link"
import { Logo } from "@/components/common/Logo"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
} from "@/components/ui/sidebar"
import type { UserPublic } from "@/lib/api"
import { Main, type NavItem } from "./Main"
import { User } from "./User"

const navItems: NavItem[] = [
  { icon: Home, title: "Dashboard", path: "/" },
  { icon: Briefcase, title: "Items", path: "/items" },
  { icon: Blocks, title: "Showcase", path: "/showcase" },
]

// Application sidebar.
export function AppSidebar({ user }: { user: UserPublic }) {
  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="px-4 py-6 group-data-[collapsible=icon]:px-0 group-data-[collapsible=icon]:items-center">
        <Link href="/">
          <Logo variant="responsive" />
        </Link>
      </SidebarHeader>
      <SidebarContent>
        <Main items={navItems} />
      </SidebarContent>
      <SidebarFooter>
        <User user={user} />
      </SidebarFooter>
    </Sidebar>
  )
}
