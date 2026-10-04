import type { ItemPublic, UserPublic } from "@/client"
import { client } from "@/client/client.gen"
import { SESSION_COOKIE } from "@/lib/config"

export const session: { token: string | undefined } = { token: "test-token" }

export class NotFound extends Error {}

export class Redirect extends Error {
  constructor(readonly url: string) {
    super(`redirect(${url})`)
  }
}

export const cookieWrites: {
  name: string
  value: string
  options: Record<string, unknown>
}[] = []

export const revalidated: [path: string, type: string | undefined][] = []

export const cookieStore = {
  get: (name: string) =>
    name === SESSION_COOKIE && session.token
      ? { name, value: session.token }
      : undefined,
  set: (name: string, value: string, options: Record<string, unknown>) => {
    cookieWrites.push({ name, value, options })
    session.token = value
  },
  delete: (name: string) => {
    if (name === SESSION_COOKIE) session.token = undefined
  },
}

// Resets the fake session and the recorded server effects.
export function resetServer() {
  session.token = "test-token"
  cookieWrites.length = 0
  revalidated.length = 0
}

export const ITEM = {
  id: "0f8fad5b-d9cb-469f-a165-70867728950e",
  owner_id: "6dfc5bca-8013-429d-996e-5b0e50de044c",
  title: "A title",
  description: null,
  created_at: "2026-10-03T12:00:00Z",
} satisfies ItemPublic

export const USER = {
  id: "6dfc5bca-8013-429d-996e-5b0e50de044c",
  email: "user@example.com",
  full_name: "A User",
  is_active: true,
  is_superuser: false,
  created_at: "2026-10-03T12:00:00Z",
} satisfies UserPublic

export type RecordedRequest = {
  url: string
  method: string
  authorization: string | null
  contentType: string | null
  body: string
}

// Stubs the client's fetch and records its requests.
export function stubFetch(reply: () => Response | Promise<Response>) {
  const requests: RecordedRequest[] = []
  const stub = async (input: RequestInfo | URL, init?: RequestInit) => {
    const request = new Request(input, init)
    requests.push({
      url: request.url,
      method: request.method,
      authorization: request.headers.get("authorization"),
      contentType: request.headers.get("content-type"),
      body: await request.clone().text(),
    })
    return reply()
  }
  client.setConfig({ fetch: Object.assign(stub, { preconnect: () => {} }) })
  return requests
}
