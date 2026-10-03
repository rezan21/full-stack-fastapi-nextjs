"use server"

import { revalidatePath } from "next/cache"
import { redirect } from "next/navigation"
import { type ActionResult, toError } from "@/lib/action-result"
import {
  changePassword as apiChangePassword,
  deleteAccount as apiDeleteAccount,
  updateProfile as apiUpdateProfile,
  type UpdatePassword,
  type UserUpdateMe,
} from "@/lib/api"
import { deleteSession, getToken } from "@/lib/session"

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

export async function changePassword(
  data: UpdatePassword,
): Promise<ActionResult> {
  if (!(await getToken())) return { error: "Not authenticated" }
  try {
    await apiChangePassword(data)
    return {}
  } catch (e) {
    return toError(e)
  }
}

export async function deleteAccount(): Promise<ActionResult> {
  if (!(await getToken())) return { error: "Not authenticated" }
  try {
    await apiDeleteAccount()
  } catch (e) {
    return toError(e)
  }
  await deleteSession()
  redirect("/login")
}
