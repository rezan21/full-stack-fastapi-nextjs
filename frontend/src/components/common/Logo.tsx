import Image, { type StaticImageData } from "next/image"
import iconLightMode from "@/assets/images/fastapi-icon.svg"
import iconDarkMode from "@/assets/images/fastapi-icon-light.svg"
import logoLightMode from "@/assets/images/fastapi-logo.svg"
import logoDarkMode from "@/assets/images/fastapi-logo-light.svg"
import { cn } from "@/lib/utils"

type Mode = "light" | "dark"

const IMAGES: Record<
  "full" | "icon",
  {
    src: Record<Mode, StaticImageData>
    width: number
    height: number
    className: string
  }
> = {
  full: {
    src: { light: logoLightMode, dark: logoDarkMode },
    width: 341,
    height: 64,
    className: "h-6 w-auto",
  },
  icon: {
    src: { light: iconLightMode, dark: iconDarkMode },
    width: 500,
    height: 500,
    className: "size-5",
  },
}

const MODE_CLASSES: Record<Mode, string> = {
  light: "dark:hidden",
  dark: "hidden dark:block",
}

// Logo image in both color modes, of which the theme shows one.
function LogoImage({
  name,
  className,
}: {
  name: keyof typeof IMAGES
  className?: string
}) {
  const image = IMAGES[name]
  return (
    <>
      {(["light", "dark"] as const).map((mode) => (
        <Image
          key={mode}
          src={image.src[mode]}
          alt="FastAPI"
          width={image.width}
          height={image.height}
          unoptimized
          className={cn(image.className, MODE_CLASSES[mode], className)}
        />
      ))}
    </>
  )
}

// Application logo.
export function Logo({
  variant = "full",
  className,
}: {
  variant?: "full" | "responsive"
  className?: string
}) {
  if (variant === "full") return <LogoImage name="full" className={className} />

  return (
    <>
      <span className="contents group-data-[collapsible=icon]:hidden">
        <LogoImage name="full" className={className} />
      </span>
      <span className="hidden group-data-[collapsible=icon]:contents">
        <LogoImage name="icon" className={className} />
      </span>
    </>
  )
}
