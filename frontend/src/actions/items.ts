"use server"

import { revalidatePath } from "next/cache"
import {
  ApiError,
  createItem as apiCreateItem,
  deleteItem as apiDeleteItem,
  updateItem as apiUpdateItem,
  type ItemCreate,
  type ItemUpdate,
} from "@/lib/api"
import { getToken } from "@/lib/session"

type ActionResult = { error?: string }

function toError(e: unknown): ActionResult {
  return { error: e instanceof ApiError ? e.message : "Something went wrong." }
}

export async function createItem(data: ItemCreate): Promise<ActionResult> {
  if (!(await getToken())) return { error: "Not authenticated" }
  try {
    await apiCreateItem(data)
    revalidatePath("/items")
    return {}
  } catch (e) {
    return toError(e)
  }
}

export async function updateItem(
  id: string,
  data: ItemUpdate,
): Promise<ActionResult> {
  if (!(await getToken())) return { error: "Not authenticated" }
  try {
    await apiUpdateItem(id, data)
    revalidatePath("/items")
    return {}
  } catch (e) {
    return toError(e)
  }
}

export async function deleteItem(id: string): Promise<ActionResult> {
  if (!(await getToken())) return { error: "Not authenticated" }
  try {
    await apiDeleteItem(id)
    revalidatePath("/items")
    return {}
  } catch (e) {
    return toError(e)
  }
}
