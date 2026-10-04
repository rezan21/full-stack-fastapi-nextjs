import {
  itemsCreateItem,
  itemsDeleteItem,
  usersRegisterUser,
} from "../../src/client"
import { client } from "../../src/client/client.gen"
import { API_URL } from "../../src/lib/config"

client.setConfig({ baseUrl: API_URL })

// Registers a user through the API.
export async function createUser({
  email,
  password,
}: {
  email: string
  password: string
}) {
  const { data } = await usersRegisterUser({
    body: { email, password, full_name: "Test User" },
    throwOnError: true,
  })
  return data
}

// Deletes an item as the token's user.
export async function deleteItemAs(token: string, id: string) {
  await itemsDeleteItem({ path: { id }, auth: token, throwOnError: true })
}

// Creates items as the token's user.
export async function createItemsAs(token: string, count: number) {
  for (let number = 1; number <= count; number++) {
    await itemsCreateItem({
      body: { title: `Item ${number}` },
      auth: token,
      throwOnError: true,
    })
  }
}
