import Image from "next/image"
import { cn } from "@/lib/utils"

const IMAGES = {
  full: {
    src: {
      light: "/assets/images/fastapi-logo.svg",
      dark: "/assets/images/fastapi-logo-light.svg",
    },
    width: 341,
    height: 64,
    className: "h-6 w-auto",
  },
  icon: {
    src: {
      light: "/assets/images/fastapi-icon.svg",
      dark: "/assets/images/fastapi-icon-light.svg",
    },
    width: 500,
    height: 500,
    className: "size-5",
  },
}

const MODE_CLASSES = { light: "dark:hidden", dark: "hidden dark:block" }

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
