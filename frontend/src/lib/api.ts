import "server-only"
import { ZodError } from "zod"
import {
  type AccountDeletion,
  type ChatMessagePublic,
  type ChatRun,
  type ConversationPublic,
  chatCreateConversation,
  chatReadConversation,
  chatReadConversations,
  chatReadMessages,
  type EmailChange,
  type HttpError,
  type HttpValidationError,
  type ItemCreate,
  type ItemPublic,
  type ItemUpdate,
  itemsCreateItem,
  itemsDeleteItem,
  itemsReadItem,
  itemsReadItems,
  itemsUpdateItem,
  loginLoginAccessToken,
  loginLogout,
  loginRecoverPassword,
  loginResetPassword,
  type PasswordRecovery,
  type UpdatePassword,
  type UserPublic,
  type UserRegister,
  type UserUpdateMe,
  usersCompleteSignup,
  usersConfirmEmailChange,
  usersDeleteUserMe,
  usersReadUserMe,
  usersRegisterUser,
  usersRequestEmailChange,
  usersUpdatePasswordMe,
  usersUpdateUserMe,
} from "@/client"
import { client } from "@/client/client.gen"
import { API_URL, ITEMS_PAGE_SIZE } from "@/lib/config"
import { getToken } from "@/lib/session"

export type {
  AccountDeletion,
  ChatMessagePublic,
  ChatRun,
  ConversationPublic,
  EmailChange,
  ItemCreate,
  ItemPublic,
  ItemUpdate,
  PasswordRecovery,
  UpdatePassword,
  UserPublic,
  UserRegister,
  UserUpdateMe,
}

const FALLBACK_ERROR = "Something went wrong."

export const CHAT_RUN_PATH = "/api/v1/chat"

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

// Extracts a message from an API error.
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

// Returns a call's data, or throws an ApiError.
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

export function logout() {
  return unwrap(loginLogout())
}

export function getCurrentUser() {
  return unwrap(usersReadUserMe())
}

export function registerUser(body: UserRegister) {
  return unwrap(usersRegisterUser({ body }))
}

export function completeSignup(token: string, newPassword: string) {
  return unwrap(
    usersCompleteSignup({ body: { token, new_password: newPassword } }),
  )
}

export function confirmEmailChange(token: string) {
  return unwrap(usersConfirmEmailChange({ body: { token } }))
}

export function recoverPassword(body: PasswordRecovery) {
  return unwrap(loginRecoverPassword({ body }))
}

export function resetPassword(token: string, newPassword: string) {
  return unwrap(
    loginResetPassword({ body: { token, new_password: newPassword } }),
  )
}

export function getItem(id: string) {
  return unwrap(itemsReadItem({ path: { id } }))
}

// Fetches one page of items.
export function getItems(page: number) {
  return unwrap(
    itemsReadItems({
      query: { skip: (page - 1) * ITEMS_PAGE_SIZE, limit: ITEMS_PAGE_SIZE },
    }),
  )
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

export function requestEmailChange(body: EmailChange) {
  return unwrap(usersRequestEmailChange({ body }))
}

export function changePassword(body: UpdatePassword) {
  return unwrap(usersUpdatePasswordMe({ body }))
}

export function deleteAccount(body: AccountDeletion) {
  return unwrap(usersDeleteUserMe({ body }))
}

export function createConversation() {
  return unwrap(chatCreateConversation())
}

export function getConversations() {
  return unwrap(chatReadConversations())
}

export function getConversation(id: string) {
  return unwrap(chatReadConversation({ path: { id } }))
}

export function getConversationMessages(id: string) {
  return unwrap(chatReadMessages({ path: { id } }))
}

// Starts a chat run and returns the API's response, a live stream when it succeeds.
export async function streamChat(
  body: ChatRun,
  signal: AbortSignal,
): Promise<Response> {
  const { error, response } = await client.post({
    url: CHAT_RUN_PATH,
    body,
    signal,
    parseAs: "stream",
    security: [{ scheme: "bearer", type: "http" }],
    headers: { "Content-Type": "application/json" },
  })
  if (!response) throw error
  if (response.ok) return response
  const retryAfter = response.headers.get("retry-after")
  return Response.json(error ?? {}, {
    status: response.status,
    headers: retryAfter ? { "retry-after": retryAfter } : undefined,
  })
}
