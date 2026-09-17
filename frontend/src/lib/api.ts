import { getToken } from "@/lib/session"

const API_BASE = `${process.env.API_URL ?? "http://localhost:8000"}/api/v1`

export type UserPublic = {
  id: string
  email: string
  is_active: boolean
  is_superuser: boolean
  full_name: string | null
  created_at?: string | null
}

export type ItemPublic = {
  id: string
  title: string
  description: string | null
  owner_id: string
  created_at?: string | null
}

export type ItemsPublic = { data: ItemPublic[]; count: number }
export type ItemCreate = { title: string; description?: string | null }
export type ItemUpdate = { title?: string; description?: string | null }

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function parseError(res: Response): Promise<string> {
  try {
    const body = await res.json()
    const detail = body?.detail
    if (typeof detail === "string") return detail
    if (Array.isArray(detail) && detail.length > 0) {
      return detail[0]?.msg ?? "Something went wrong."
    }
  } catch {
    // fall through to status text
  }
  return res.statusText || "Something went wrong."
}

type RequestOptions = {
  method?: string
  body?: unknown
  form?: Record<string, string>
  auth?: boolean
}

async function request<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { method = "GET", body, form, auth = true } = options
  const headers: Record<string, string> = {}
  let payload: BodyInit | undefined

  if (auth) {
    const token = await getToken()
    if (token) headers.Authorization = `Bearer ${token}`
  }
  if (form) {
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    payload = new URLSearchParams(form).toString()
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json"
    payload = JSON.stringify(body)
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: payload,
    cache: "no-store",
  })

  if (!res.ok) throw new ApiError(await parseError(res), res.status)
  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

export function loginAccessToken(username: string, password: string) {
  return request<{ access_token: string; token_type: string }>(
    "/login/access-token",
    { method: "POST", auth: false, form: { username, password } },
  )
}

export function getCurrentUser() {
  return request<UserPublic>("/users/me")
}

export function registerUser(body: {
  email: string
  password: string
  full_name: string
}) {
  return request<UserPublic>("/users/signup", {
    method: "POST",
    auth: false,
    body,
  })
}

export function recoverPassword(email: string) {
  return request<{ message: string }>(
    `/password-recovery/${encodeURIComponent(email)}`,
    { method: "POST", auth: false },
  )
}

export function resetPassword(token: string, newPassword: string) {
  return request<{ message: string }>("/reset-password/", {
    method: "POST",
    auth: false,
    body: { token, new_password: newPassword },
  })
}

export function getItems() {
  return request<ItemsPublic>("/items/?skip=0&limit=100")
}

export function createItem(body: ItemCreate) {
  return request<ItemPublic>("/items/", { method: "POST", body })
}

export function updateItem(id: string, body: ItemUpdate) {
  return request<ItemPublic>(`/items/${id}`, { method: "PUT", body })
}

export function deleteItem(id: string) {
  return request<{ message: string }>(`/items/${id}`, { method: "DELETE" })
}
