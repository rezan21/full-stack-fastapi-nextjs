"use server"

import { revalidatePath } from "next/cache"
import { redirect } from "next/navigation"
import { type ActionResult, authenticated } from "@/lib/action-result"
import {
  type AccountDeletion,
  changePassword as apiChangePassword,
  deleteAccount as apiDeleteAccount,
  requestEmailChange as apiRequestEmailChange,
  updateProfile as apiUpdateProfile,
  type EmailChange,
  type UpdatePassword,
  type UserUpdateMe,
} from "@/lib/api"
import { createSession, deleteSession } from "@/lib/session"

// Updates the current user's profile.
export async function updateProfile(data: UserUpdateMe): Promise<ActionResult> {
  return authenticated(async () => {
    await apiUpdateProfile(data)
    revalidatePath("/", "layout")
  })
}

// Requests the link that confirms a new email address.
export async function changeEmail(data: EmailChange): Promise<ActionResult> {
  return authenticated(() => apiRequestEmailChange(data))
}

// Changes the current user's password.
export async function changePassword(
  data: UpdatePassword,
): Promise<ActionResult> {
  return authenticated(async () => {
    const { access_token, expires_in } = await apiChangePassword(data)
    await createSession(access_token, expires_in)
  })
}

// Deletes the current user's account.
export async function deleteAccount(
  data: AccountDeletion,
): Promise<ActionResult> {
  const result = await authenticated(() => apiDeleteAccount(data))
  if (result.error) return result
  await deleteSession()
  redirect("/login")
}
