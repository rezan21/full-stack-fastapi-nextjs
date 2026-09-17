"use server"

import { redirect } from "next/navigation"
import {
  ApiError,
  recoverPassword as apiRecoverPassword,
  resetPassword as apiResetPassword,
  loginAccessToken,
  registerUser,
} from "@/lib/api"
import { createSession, deleteSession } from "@/lib/session"

type ActionResult = { error?: string }

function toError(e: unknown): ActionResult {
  return { error: e instanceof ApiError ? e.message : "Something went wrong." }
}

export async function login(
  username: string,
  password: string,
): Promise<ActionResult> {
  try {
    const { access_token } = await loginAccessToken(username, password)
    await createSession(access_token)
    return {}
  } catch (e) {
    return toError(e)
  }
}

export async function logout(): Promise<void> {
  await deleteSession()
  redirect("/login")
}

export async function signup(data: {
  full_name: string
  email: string
  password: string
}): Promise<ActionResult> {
  try {
    await registerUser(data)
    return {}
  } catch (e) {
    return toError(e)
  }
}

export async function recoverPassword(email: string): Promise<ActionResult> {
  try {
    await apiRecoverPassword(email)
    return {}
  } catch (e) {
    return toError(e)
  }
}

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
