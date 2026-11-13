import { expect, test } from "@playwright/test"
import type { ChatSession } from "../src/entities/chat/chat-session"
import copy from "../src/shared/i18n/locales/ru/chat.json" with { type: "json" }

const session: ChatSession = {
  version: 1,
  id: "scroll-regression",
  title: "Scroll regression",
  createdAt: 1,
  updatedAt: 1,
  draft: "",
  status: "done",
  error: null,
  messages: Array.from({ length: 12 }, (_, index) => ({
    id: `message-${index}`,
    role: index % 2 === 0 ? "user" : "assistant",
    content:
      index % 2 === 0
        ? `Question ${index}`
        : Array.from(
            { length: 12 },
            (_, paragraph) =>
              `Paragraph ${paragraph}: The regional transport network connects settlements and markets. Travel time changes the accessibility estimate.`,
          ).join("\n\n"),
    complete: true,
    steps: [],
    tables: [],
    charts: [],
    mapCommands: [],
  })),
}

test.beforeEach(async ({ page }) => {
  await page.addInitScript((saved) => {
    const key = `plexus.chat.session.v1.${saved.id}`
    if (!localStorage.getItem(key)) localStorage.setItem(key, JSON.stringify(saved))
    localStorage.setItem("plexus.chat.active.v1", saved.id)
  }, session)
  await page.goto("/")
})

test("reads earlier messages with the wheel after scrolling to the end", async ({ page }) => {
  const history = page.getByRole("region", { name: copy.history })
  await expect(history).toBeVisible()
  await expect
    .poll(() => history.evaluate((node) => node.scrollHeight - node.clientHeight))
    .toBeGreaterThan(1000)
  await history.hover()
  await page.mouse.wheel(0, 20000)
  await expect
    .poll(() => history.evaluate((node) => node.scrollHeight - node.clientHeight - node.scrollTop))
    .toBeLessThan(3)
  const bottom = await history.evaluate((node) => node.scrollTop)
  await page.mouse.wheel(0, -500)
  await expect.poll(() => history.evaluate((node) => node.scrollTop)).toBeLessThan(bottom - 100)
  const reading = await history.evaluate((node) => node.scrollTop)
  await page.waitForTimeout(700)
  expect(await history.evaluate((node) => node.scrollTop)).toBeLessThanOrEqual(reading + 2)
  await page.mouse.wheel(0, -20000)
  await expect.poll(() => history.evaluate((node) => node.scrollTop)).toBeLessThan(3)
})

test("reads earlier messages with the keyboard after scrolling to the end", async ({ page }) => {
  const history = page.getByRole("region", { name: copy.history })
  await expect(history).toBeVisible()
  await history.focus()
  await page.keyboard.press("Control+End")
  await expect
    .poll(() => history.evaluate((node) => node.scrollHeight - node.clientHeight - node.scrollTop))
    .toBeLessThan(3)
  const bottom = await history.evaluate((node) => node.scrollTop)
  await page.keyboard.press("PageUp")
  await expect.poll(() => history.evaluate((node) => node.scrollTop)).toBeLessThan(bottom - 100)
  await page.keyboard.press("Control+Home")
  await expect.poll(() => history.evaluate((node) => node.scrollTop)).toBeLessThan(3)
})

test("scrolls the conversation upward while the pointer is over a result table", async ({
  page,
}) => {
  const message = session.messages.at(-1)
  if (!message) throw new Error("Completed reply is missing")
  const saved: ChatSession = {
    ...session,
    messages: [
      {
        ...message,
        tables: [
          {
            id: "settlements",
            title: "settlements",
            caption: "Settlements",
            columns: [
              { key: "name", format: "text" },
              { key: "population", format: "integer" },
            ],
            rows: Array.from({ length: 8 }, (_, index) => ({
              id: String(index),
              name: `Settlement ${index}`,
              population: 1000 + index,
            })),
            total: 8,
            truncated: false,
            source: "/api/v1/regions",
          },
        ],
      },
    ],
  }
  await page.evaluate((value) => {
    localStorage.setItem(`plexus.chat.session.v1.${value.id}`, JSON.stringify(value))
  }, saved)
  await page.reload()
  const history = page.getByRole("region", { name: copy.history })
  await expect(history).toBeVisible()
  await expect
    .poll(() => history.evaluate((node) => node.scrollHeight - node.clientHeight - node.scrollTop))
    .toBeLessThan(3)
  const bottom = await history.evaluate((node) => node.scrollTop)
  expect(bottom).toBeGreaterThan(500)
  await history.getByRole("cell", { name: "Settlement 6", exact: true }).hover()
  await page.mouse.wheel(0, -500)
  await expect.poll(() => history.evaluate((node) => node.scrollTop)).toBeLessThan(bottom - 100)
})
