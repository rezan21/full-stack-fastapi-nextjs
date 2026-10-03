import { itemsDeleteItem, usersRegisterUser } from "../../src/client"
import { client } from "../../src/client/client.gen"
import { API_URL } from "../../src/lib/config"

client.setConfig({ baseUrl: API_URL })

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

export async function deleteItemAs(token: string, id: string) {
  await itemsDeleteItem({ path: { id }, auth: token, throwOnError: true })
}
