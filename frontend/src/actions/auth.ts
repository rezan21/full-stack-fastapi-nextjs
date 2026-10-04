"use server"

import { revalidatePath } from "next/cache"
import { redirect } from "next/navigation"
import { type ActionResult, toError } from "@/lib/action-result"
import {
  completeSignup as apiCompleteSignup,
  confirmEmailChange as apiConfirmEmailChange,
  logout as apiLogout,
  recoverPassword as apiRecoverPassword,
  resetPassword as apiResetPassword,
  loginAccessToken,
  type PasswordRecovery,
  registerUser,
  type UserRegister,
} from "@/lib/api"
import { createSession, deleteSession } from "@/lib/session"

// Signs a user in.
export async function login(
  username: string,
  password: string,
): Promise<ActionResult> {
  try {
    const { access_token, expires_in } = await loginAccessToken(
      username,
      password,
    )
    await createSession(access_token, expires_in)
    return {}
  } catch (e) {
    return toError(e)
  }
}

// Signs the current user out.
export async function logout(): Promise<void> {
  await apiLogout().catch(() => undefined)
  await deleteSession()
  redirect("/login")
}

// Requests the link that completes a sign-up.
export async function signup(data: UserRegister): Promise<ActionResult> {
  try {
    await registerUser(data)
    return {}
  } catch (e) {
    return toError(e)
  }
}

// Creates the user a sign-up link was sent for.
export async function completeSignup(
  token: string,
  password: string,
): Promise<ActionResult> {
  try {
    await apiCompleteSignup(token, password)
    return {}
  } catch (e) {
    return toError(e)
  }
}

// Applies a confirmed email change.
export async function confirmEmailChange(token: string): Promise<ActionResult> {
  try {
    await apiConfirmEmailChange(token)
  } catch (e) {
    return toError(e)
  }
  revalidatePath("/", "layout")
  return {}
}

// Starts a password recovery.
export async function recoverPassword(
  data: PasswordRecovery,
): Promise<ActionResult> {
  try {
    await apiRecoverPassword(data)
    return {}
  } catch (e) {
    return toError(e)
  }
}

// Completes a password reset.
export async function resetPassword(
  token: string,
  newPassword: string,
): Promise<ActionResult> {
  try {
    await apiResetPassword(token, newPassword)
    return {}
  } catch (e) {
    return toError(e)
  }
}
