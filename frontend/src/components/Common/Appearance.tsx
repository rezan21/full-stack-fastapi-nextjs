"use client"

import { Monitor, Moon, Sun } from "lucide-react"
import { useTheme } from "next-themes"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

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

export function AppearanceSubmenu() {
  const { theme } = useTheme()
  const Icon = ICON_MAP[theme as keyof typeof ICON_MAP] ?? Monitor

  return (
    <DropdownMenuSub>
      <DropdownMenuSubTrigger data-testid="theme-button">
        <Icon />
        Appearance
      </DropdownMenuSubTrigger>
      <DropdownMenuSubContent>
        <ThemeItems />
      </DropdownMenuSubContent>
    </DropdownMenuSub>
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
