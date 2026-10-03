"use client"

import { Blocks, Briefcase, Home } from "lucide-react"
import { Logo } from "@/components/Common/Logo"
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

export function AppSidebar({ user }: { user: UserPublic }) {
  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="px-4 py-6 group-data-[collapsible=icon]:px-0 group-data-[collapsible=icon]:items-center">
        <Logo variant="responsive" />
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
