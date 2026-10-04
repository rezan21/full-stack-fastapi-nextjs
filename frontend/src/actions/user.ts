"use server"

import { revalidatePath } from "next/cache"
import { redirect } from "next/navigation"
import { type ActionResult, toError } from "@/lib/action-result"
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
import { createSession, deleteSession, getToken } from "@/lib/session"

// Updates the current user's profile.
export async function updateProfile(data: UserUpdateMe): Promise<ActionResult> {
  if (!(await getToken())) return { error: "Not authenticated" }
  try {
    await apiUpdateProfile(data)
  } catch (e) {
    return toError(e)
  }
  revalidatePath("/", "layout")
  return {}
}

// Requests the link that confirms a new email address.
export async function changeEmail(data: EmailChange): Promise<ActionResult> {
  if (!(await getToken())) return { error: "Not authenticated" }
  try {
    await apiRequestEmailChange(data)
    return {}
  } catch (e) {
    return toError(e)
  }
}

// Changes the current user's password.
export async function changePassword(
  data: UpdatePassword,
): Promise<ActionResult> {
  if (!(await getToken())) return { error: "Not authenticated" }
  try {
    const { access_token, expires_in } = await apiChangePassword(data)
    await createSession(access_token, expires_in)
    return {}
  } catch (e) {
    return toError(e)
  }
}

// Deletes the current user's account.
export async function deleteAccount(
  data: AccountDeletion,
): Promise<ActionResult> {
  if (!(await getToken())) return { error: "Not authenticated" }
  try {
    await apiDeleteAccount(data)
  } catch (e) {
    return toError(e)
  }
  await deleteSession()
  redirect("/login")
}
