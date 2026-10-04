import Link from "next/link"
import { Footer } from "@/components/common/Footer"
import { Logo } from "@/components/common/Logo"
import { Button } from "@/components/ui/button"
import { getToken } from "@/lib/session"

// Landing page.
export default async function Page() {
  const signedIn = Boolean(await getToken())

  return (
    <div className="flex min-h-svh flex-col">
      <header className="flex h-16 items-center justify-between border-b px-6">
        <Link href="/">
          <Logo />
        </Link>
        <Button
          render={<Link href={signedIn ? "/dashboard" : "/login"} />}
          nativeButton={false}
        >
          {signedIn ? "Dashboard" : "Log in"}
        </Button>
      </header>
      <main className="flex flex-1 flex-col items-center justify-center gap-4 p-6 text-center">
        <h1 className="text-4xl font-bold tracking-tight">
          Full Stack FastAPI Template
        </h1>
        <p className="max-w-xl text-muted-foreground">
          A FastAPI and Next.js starter with authentication, a typed API client
          and a ready-made dashboard.
        </p>
      </main>
      <Footer />
    </div>
  )
}
