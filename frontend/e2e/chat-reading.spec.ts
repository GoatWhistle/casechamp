import AxeBuilder from "@axe-core/playwright"
import { expect, test } from "@playwright/test"
import chat from "../src/shared/i18n/locales/ru/chat.json" with { type: "json" }

test("long saved replies retain their title and reading position as content grows", async ({
  page,
}, testInfo) => {
  const title = "First question topic"
  await page.addInitScript((savedTitle) => {
    const message = {
      complete: true,
      steps: [],
      tables: [],
      charts: [],
      mapCommands: [],
    }
    const session = {
      version: 1,
      id: "reading-check",
      title: savedTitle,
      createdAt: Date.now(),
      updatedAt: Date.now(),
      draft: "",
      status: "done",
      error: null,
      messages: [
        { ...message, id: "question", role: "user", content: "First question" },
        {
          ...message,
          id: "reply",
          role: "assistant",
          content: Array.from(
            { length: 45 },
            (_, index) => `Paragraph ${index + 1}: reading a long reply.`,
          ).join("\n\n"),
        },
      ],
    }
    localStorage.setItem("plexus.chat.session.v1.reading-check", JSON.stringify(session))
    localStorage.setItem("plexus.chat.active.v1", session.id)
  }, title)
  await page.goto("/")
  await expect(page.getByText(title, { exact: true })).toBeVisible()
  const scroll = page.getByRole("region", { name: chat.history })
  await expect(scroll).toBeVisible()
  await expect.poll(() => scroll.evaluate((node) => node.scrollTop)).toBeGreaterThan(100)
  await scroll.hover()
  await page.mouse.wheel(0, -40)
  await expect
    .poll(() => scroll.evaluate((node) => node.scrollHeight - node.scrollTop - node.clientHeight))
    .toBeGreaterThan(2)
  const before = await scroll.evaluate((node) => node.scrollTop)
  await scroll.evaluate((node) => {
    const paragraph = document.createElement("p")
    paragraph.textContent = "The answer continues. ".repeat(100)
    node.firstElementChild?.append(paragraph)
  })
  await page.waitForTimeout(250)
  expect(await scroll.evaluate((node) => node.scrollTop)).toBeCloseTo(before, 0)
  await page.screenshot({ path: testInfo.outputPath("reading-1440.png") })
  const accessibility = await new AxeBuilder({ page }).include("figure").include("aside").analyze()
  expect(accessibility.violations).toEqual([])
  await page.reload()
  await expect(page.getByText(title, { exact: true })).toBeVisible()
})
