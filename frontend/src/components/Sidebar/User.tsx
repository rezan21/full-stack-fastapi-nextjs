"use client"

import { ChevronsUpDown, LogOut, Settings } from "lucide-react"
import Link from "next/link"
import { logout } from "@/actions/auth"
import { AppearanceSubmenu } from "@/components/Common/Appearance"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar"
import type { UserPublic } from "@/lib/api"
import { getInitials } from "@/lib/utils"

function UserInfo({
  fullName,
  email,
}: {
  fullName?: string | null
  email?: string
}) {
  return (
    <div className="flex items-center gap-2.5 w-full min-w-0">
      <Avatar>
        <AvatarFallback>{getInitials(fullName || "User")}</AvatarFallback>
      </Avatar>
      <div className="flex flex-col items-start min-w-0">
        <p className="text-sm font-medium truncate w-full">{fullName}</p>
        <p className="text-xs text-muted-foreground truncate w-full">{email}</p>
      </div>
    </div>
  )
}

export function User({ user }: { user: UserPublic }) {
  const { isMobile, setOpenMobile } = useSidebar()

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger
            render={
              <SidebarMenuButton
                size="lg"
                className="hover:bg-sidebar-accent/50 aria-expanded:bg-sidebar-accent aria-expanded:text-sidebar-accent-foreground"
                data-testid="user-menu"
              />
            }
          >
            <UserInfo fullName={user.full_name} email={user.email} />
            <ChevronsUpDown className="ml-auto text-muted-foreground" />
          </DropdownMenuTrigger>
          <DropdownMenuContent
            className="w-(--anchor-width) min-w-56 rounded-lg"
            side={isMobile ? "bottom" : "right"}
            align="end"
            sideOffset={4}
          >
            <DropdownMenuGroup>
              <DropdownMenuLabel className="p-0 font-normal">
                <UserInfo fullName={user.full_name} email={user.email} />
              </DropdownMenuLabel>
            </DropdownMenuGroup>
            <DropdownMenuSeparator />
            <DropdownMenuGroup>
              <DropdownMenuItem
                render={<Link href="/settings" />}
                onClick={() => isMobile && setOpenMobile(false)}
              >
                <Settings />
                Settings
              </DropdownMenuItem>
              <AppearanceSubmenu />
            </DropdownMenuGroup>
            <DropdownMenuSeparator />
            <DropdownMenuGroup>
              <DropdownMenuItem onClick={() => logout()}>
                <LogOut />
                Log out
              </DropdownMenuItem>
            </DropdownMenuGroup>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  )
}
