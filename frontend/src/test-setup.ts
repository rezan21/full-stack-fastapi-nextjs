import { mock } from "bun:test"
import { cookieStore, NotFound, Redirect, revalidated } from "@/test-support"

mock.module("server-only", () => ({}))
mock.module("next/headers", () => ({ cookies: async () => cookieStore }))
mock.module("next/cache", () => ({
  revalidatePath: (path: string, type?: string) => {
    revalidated.push([path, type])
  },
}))
mock.module("next/navigation", () => ({
  notFound: () => {
    throw new NotFound("notFound() called")
  },
  redirect: (url: string) => {
    throw new Redirect(url)
  },
}))
