"use server"

import { revalidatePath } from "next/cache"
import { type ActionResult, authenticated } from "@/lib/action-result"
import {
  createItem as apiCreateItem,
  deleteItem as apiDeleteItem,
  updateItem as apiUpdateItem,
  type ItemCreate,
  type ItemUpdate,
} from "@/lib/api"

// Creates an item.
export async function createItem(data: ItemCreate): Promise<ActionResult> {
  return authenticated(async () => {
    await apiCreateItem(data)
    revalidatePath("/items", "layout")
  })
}

// Updates an item.
export async function updateItem(
  id: string,
  data: ItemUpdate,
): Promise<ActionResult> {
  return authenticated(async () => {
    await apiUpdateItem(id, data)
    revalidatePath("/items", "layout")
  })
}

// Deletes an item.
export async function deleteItem(id: string): Promise<ActionResult> {
  return authenticated(async () => {
    await apiDeleteItem(id)
    revalidatePath("/items", "layout")
  })
}
