import { expect, type Page, test } from "@playwright/test"
import { CHAT_MESSAGE_MAX_LENGTH, CHAT_RUN_URL } from "../src/lib/config"
import { createConversationAs, createUser } from "./utils/api"
import { randomEmail, randomPassword } from "./utils/random"
import { logInUser, sessionToken } from "./utils/user"

const events = (threadId: string, text: string) =>
  [
    { type: "RUN_STARTED", threadId, runId: "run-1" },
    { type: "TEXT_MESSAGE_START", messageId: "answer-1", role: "assistant" },
    { type: "TEXT_MESSAGE_CONTENT", messageId: "answer-1", delta: text },
    { type: "TEXT_MESSAGE_END", messageId: "answer-1" },
    { type: "RUN_FINISHED", threadId, runId: "run-1" },
  ]
    .map((event) => `data: ${JSON.stringify(event)}\n\n`)
    .join("")

// Starts a conversation through the UI and returns its id.
async function startChat(page: Page) {
  await page.goto("/chat")
  await page.getByRole("button", { name: "New chat" }).first().click()
  await page.waitForURL(/\/chat\/[0-9a-f-]{36}$/)
  return page.url().split("/chat/")[1]
}

test.describe("AI Chat", () => {
  test.use({ storageState: { cookies: [], origins: [] } })
  let email: string
  const password = randomPassword()

  test.beforeAll(async () => {
    email = randomEmail()
    await createUser({ email, password })
  })

  test.beforeEach(async ({ page }) => {
    await logInUser(page, email, password)
  })

  test("the sidebar leads to the chat, where a new conversation opens", async ({
    page,
  }) => {
    await page.getByRole("link", { name: "AI Chat" }).click()
    await expect(page).toHaveURL("/chat")
    await expect(page.getByRole("heading", { name: "AI Chat" })).toBeVisible()

    await page.getByRole("button", { name: "New chat" }).first().click()

    await page.waitForURL(/\/chat\/[0-9a-f-]{36}$/)
    await expect(page.getByRole("textbox", { name: "Message" })).toBeVisible()
  })

  test("a message gets a streamed answer, and only the newest message is sent", async ({
    page,
  }) => {
    const id = await startChat(page)
    const sent: unknown[] = []
    await page.route(`**${CHAT_RUN_URL}`, async (route) => {
      sent.push(route.request().postDataJSON())
      await route.fulfill({
        status: 200,
        headers: { "content-type": "text/event-stream" },
        body: events(id, `You said: ${sent.length}`),
      })
    })

    const box = page.getByRole("textbox", { name: "Message" })
    await box.fill("What is FastAPI?")
    await box.press("Enter")
    await expect(page.getByText("What is FastAPI?")).toBeVisible()
    await expect(page.getByText("You said: 1")).toBeVisible()
    await box.fill("And Next.js?")
    await box.press("Enter")
    await expect(page.getByText("You said: 2")).toBeVisible()

    expect(sent).toHaveLength(2)
    for (const [index, body] of (sent as Record<string, unknown>[]).entries()) {
      expect(body.threadId).toBe(id)
      expect(body.state).toEqual({})
      const messages = body.messages as { role: string; content: string }[]
      expect(messages).toHaveLength(1)
      expect(messages[0]).toMatchObject({
        role: "user",
        content: index === 0 ? "What is FastAPI?" : "And Next.js?",
      })
    }
  })

  test("a refusal from the API is shown to the user", async ({ page }) => {
    await startChat(page)
    await page.route(`**${CHAT_RUN_URL}`, (route) =>
      route.fulfill({
        status: 429,
        headers: { "retry-after": "1800" },
        json: { detail: "Too many messages. Try again in 30 minutes." },
      }),
    )

    const box = page.getByRole("textbox", { name: "Message" })
    await box.fill("One more")
    await box.press("Enter")

    await expect(
      page.getByText("Too many messages. Try again in 30 minutes."),
    ).toBeVisible()
    await expect(box).toBeEnabled()
    await expect(box).toHaveValue("One more")
    await expect(page.locator('[data-slot="message"]')).toHaveCount(0)
  })

  test("a message over the length limit shows a counter and cannot be sent", async ({
    page,
  }) => {
    await startChat(page)
    let sent = 0
    await page.route(`**${CHAT_RUN_URL}`, (route) => {
      sent++
      return route.abort()
    })
    const box = page.getByRole("textbox", { name: "Message" })
    const send = page.getByRole("button", { name: "Send" })
    const limit = CHAT_MESSAGE_MAX_LENGTH.toLocaleString("en-US")

    await box.fill("x".repeat(100))
    await expect(page.getByText(`/ ${limit}`)).toHaveCount(0)

    await box.fill("x".repeat(CHAT_MESSAGE_MAX_LENGTH + 1))
    await expect(page.getByText(`4,001 / ${limit}`)).toBeVisible()
    await expect(send).toBeDisabled()
    await box.press("Enter")
    expect(sent).toBe(0)

    await box.fill("x".repeat(CHAT_MESSAGE_MAX_LENGTH))
    await expect(page.getByText(`${limit} / ${limit}`)).toBeVisible()
    await expect(send).toBeEnabled()
  })

  test("stopping an answer ends it without an error", async ({ page }) => {
    await startChat(page)
    await page.route(`**${CHAT_RUN_URL}`, async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 4000))
      await route.abort().catch(() => undefined)
    })

    const box = page.getByRole("textbox", { name: "Message" })
    await box.fill("Write a very long essay")
    await box.press("Enter")
    await page.getByRole("button", { name: "Stop" }).click()

    await expect(page.getByRole("button", { name: "Send" })).toBeVisible()
    await expect(page.locator('[data-slot="alert"]')).toHaveCount(0)
    await expect(page.getByText("Write a very long essay")).toBeVisible()
  })

  test("past conversations are listed and can be reopened", async ({
    page,
  }) => {
    const id = await createConversationAs(await sessionToken(page))

    await page.goto("/chat")
    await page.locator(`a[href="/chat/${id}"]`).click()

    await expect(page).toHaveURL(`/chat/${id}`)
    await expect(page.getByRole("textbox", { name: "Message" })).toBeVisible()
  })

  test("nobody else can open a conversation", async ({ page, browser }) => {
    const id = await createConversationAs(await sessionToken(page))
    const intruderEmail = randomEmail()
    await createUser({ email: intruderEmail, password })
    const context = await browser.newContext()
    const intruder = await context.newPage()
    await logInUser(intruder, intruderEmail, password)

    await intruder.goto(`/chat/${id}`)

    await expect(
      intruder.getByRole("heading", { name: "Page not found" }),
    ).toBeVisible()
    await context.close()
  })
})
