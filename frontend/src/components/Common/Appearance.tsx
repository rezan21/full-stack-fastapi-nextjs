"use client"

import { Monitor, Moon, Sun } from "lucide-react"
import { useTheme } from "next-themes"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar"

const ICON_MAP = {
  system: Monitor,
  light: Sun,
  dark: Moon,
} as const

function ThemeItems() {
  const { setTheme } = useTheme()

  return (
    <DropdownMenuGroup>
      <DropdownMenuItem
        data-testid="light-mode"
        onClick={() => setTheme("light")}
      >
        <Sun />
        Light
      </DropdownMenuItem>
      <DropdownMenuItem
        data-testid="dark-mode"
        onClick={() => setTheme("dark")}
      >
        <Moon />
        Dark
      </DropdownMenuItem>
      <DropdownMenuItem onClick={() => setTheme("system")}>
        <Monitor />
        System
      </DropdownMenuItem>
    </DropdownMenuGroup>
  )
}

export function SidebarAppearance() {
  const { isMobile } = useSidebar()
  const { theme } = useTheme()
  const Icon = ICON_MAP[(theme as keyof typeof ICON_MAP) ?? "system"] ?? Monitor

  return (
    <SidebarMenuItem>
      <DropdownMenu modal={false}>
        <DropdownMenuTrigger
          render={
            <SidebarMenuButton
              tooltip="Appearance"
              className="hover:bg-sidebar-accent/50"
              data-testid="theme-button"
            />
          }
        >
          <Icon className="text-muted-foreground" />
          <span>Appearance</span>
          <span className="sr-only">Toggle theme</span>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          side={isMobile ? "top" : "right"}
          align="end"
          className="w-(--anchor-width) min-w-56"
        >
          <ThemeItems />
        </DropdownMenuContent>
      </DropdownMenu>
    </SidebarMenuItem>
  )
}

export function Appearance() {
  return (
    <div className="flex items-center justify-center">
      <DropdownMenu modal={false}>
        <DropdownMenuTrigger
          render={
            <Button data-testid="theme-button" variant="outline" size="icon" />
          }
        >
          <Sun className="rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          <span className="sr-only">Toggle theme</span>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <ThemeItems />
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}
