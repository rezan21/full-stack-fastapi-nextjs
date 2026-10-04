"use client"

import Image from "next/image"
import Link from "next/link"
import { useTheme } from "next-themes"
import { useEffect, useState } from "react"
import { cn } from "@/lib/utils"

const ASSETS = {
  full: {
    light: "/assets/images/fastapi-logo.svg",
    dark: "/assets/images/fastapi-logo-light.svg",
  },
  icon: {
    light: "/assets/images/fastapi-icon.svg",
    dark: "/assets/images/fastapi-icon-light.svg",
  },
}

interface LogoProps {
  variant?: "full" | "icon" | "responsive"
  className?: string
  asLink?: boolean
}

// Application logo.
export function Logo({
  variant = "full",
  className,
  asLink = true,
}: LogoProps) {
  const { resolvedTheme } = useTheme()
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])

  const mode = mounted && resolvedTheme === "dark" ? "dark" : "light"
  const fullLogo = ASSETS.full[mode]
  const iconLogo = ASSETS.icon[mode]

  const content =
    variant === "responsive" ? (
      <>
        <Image
          src={fullLogo}
          alt="FastAPI"
          width={341}
          height={64}
          unoptimized
          className={cn(
            "h-6 w-auto group-data-[collapsible=icon]:hidden",
            className,
          )}
        />
        <Image
          src={iconLogo}
          alt="FastAPI"
          width={500}
          height={500}
          unoptimized
          className={cn(
            "size-5 hidden group-data-[collapsible=icon]:block",
            className,
          )}
        />
      </>
    ) : variant === "full" ? (
      <Image
        src={fullLogo}
        alt="FastAPI"
        width={341}
        height={64}
        unoptimized
        className={cn("h-6 w-auto", className)}
      />
    ) : (
      <Image
        src={iconLogo}
        alt="FastAPI"
        width={500}
        height={500}
        unoptimized
        className={cn("size-5", className)}
      />
    )

  if (!asLink) return content

  return <Link href="/">{content}</Link>
}
