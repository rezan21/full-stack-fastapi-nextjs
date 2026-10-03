import "server-only"
import { ZodError } from "zod"
import {
  type HttpError,
  type HttpValidationError,
  type ItemCreate,
  type ItemPublic,
  type ItemsPublic,
  type ItemUpdate,
  itemsCreateItem,
  itemsDeleteItem,
  itemsReadItem,
  itemsReadItems,
  itemsUpdateItem,
  loginLoginAccessToken,
  loginRecoverPassword,
  loginResetPassword,
  type UpdatePassword,
  type UserPublic,
  type UserRegister,
  type UserUpdateMe,
  usersDeleteUserMe,
  usersReadUserMe,
  usersRegisterUser,
  usersUpdatePasswordMe,
  usersUpdateUserMe,
} from "@/client"
import { client } from "@/client/client.gen"
import { API_URL } from "@/lib/config"
import { getToken } from "@/lib/session"

export type {
  ItemCreate,
  ItemPublic,
  ItemsPublic,
  ItemUpdate,
  UpdatePassword,
  UserPublic,
  UserRegister,
  UserUpdateMe,
}

const FALLBACK_ERROR = "Something went wrong."

client.setConfig({
  baseUrl: API_URL,
  auth: () => getToken(),
  cache: "no-store",
})

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

type Result<T> = { data?: T; error?: unknown; response?: Response }

function errorMessage(
  error: HttpError | HttpValidationError | string,
  response: Response,
): string {
  if (typeof error === "string") {
    return error || response.statusText || FALLBACK_ERROR
  }
  if (typeof error.detail === "string") return error.detail
  return error.detail?.[0]?.msg ?? (response.statusText || FALLBACK_ERROR)
}

async function unwrap<T>(call: Promise<Result<T>>): Promise<T> {
  const { data, error, response } = await call
  if (error === undefined) return data as T
  if (error instanceof ZodError) {
    throw new ApiError(error.issues[0]?.message ?? FALLBACK_ERROR, 422)
  }
  if (!response) throw error
  throw new ApiError(
    errorMessage(error as HttpError | HttpValidationError | string, response),
    response.status,
  )
}

export function loginAccessToken(username: string, password: string) {
  return unwrap(loginLoginAccessToken({ body: { username, password } }))
}

export function getCurrentUser() {
  return unwrap(usersReadUserMe())
}

export function registerUser(body: UserRegister) {
  return unwrap(usersRegisterUser({ body }))
}

export function recoverPassword(email: string) {
  return unwrap(loginRecoverPassword({ path: { email } }))
}

export function resetPassword(token: string, newPassword: string) {
  return unwrap(
    loginResetPassword({ body: { token, new_password: newPassword } }),
  )
}

export function getItem(id: string) {
  return unwrap(itemsReadItem({ path: { id } }))
}

export function getItems() {
  return unwrap(itemsReadItems())
}

export function createItem(body: ItemCreate) {
  return unwrap(itemsCreateItem({ body }))
}

export function updateItem(id: string, body: ItemUpdate) {
  return unwrap(itemsUpdateItem({ path: { id }, body }))
}

export function deleteItem(id: string) {
  return unwrap(itemsDeleteItem({ path: { id } }))
}

export function updateProfile(body: UserUpdateMe) {
  return unwrap(usersUpdateUserMe({ body }))
}

export function changePassword(body: UpdatePassword) {
  return unwrap(usersUpdatePasswordMe({ body }))
}

export function deleteAccount() {
  return unwrap(usersDeleteUserMe())
}
