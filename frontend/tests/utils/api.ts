import { request } from "@playwright/test"
import {
  chatCreateConversation,
  itemsCreateItem,
  itemsDeleteItem,
  usersCompleteSignup,
  usersRegisterUser,
} from "../../src/client"
import { client } from "../../src/client/client.gen"
import { API_URL } from "../../src/lib/config"
import { emailedToken, waitForEmailHtml } from "./mailpit"

client.setConfig({ baseUrl: API_URL })

// Signs a user up through the API with the emailed link.
export async function createUser({
  email,
  password,
}: {
  email: string
  password: string
}) {
  await usersRegisterUser({
    body: { email, full_name: "Test User" },
    throwOnError: true,
  })
  const context = await request.newContext()
  const html = await waitForEmailHtml({
    request: context,
    query: `to:${email}`,
  }).finally(() => context.dispose())
  const { data } = await usersCompleteSignup({
    body: { token: emailedToken(html), new_password: password },
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

// Starts a conversation as the token's user and returns its id.
export async function createConversationAs(token: string) {
  const { data } = await chatCreateConversation({
    auth: token,
    throwOnError: true,
  })
  return data.id
}
