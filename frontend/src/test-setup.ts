import { mock } from "bun:test"
import { NotFound, session } from "@/test-support"

mock.module("server-only", () => ({}))
mock.module("@/lib/session", () => ({ getToken: async () => session.token }))
mock.module("next/navigation", () => ({
  notFound: () => {
    throw new NotFound("notFound() called")
  },
}))
