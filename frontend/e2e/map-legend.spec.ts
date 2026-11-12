import { expect, test } from "@playwright/test"
import data from "../src/shared/i18n/locales/ru/data.json" with { type: "json" }
import map from "../src/shared/i18n/locales/ru/map.json" with { type: "json" }

test("legend collapses to a round control and restores focus and saved size", async ({ page }) => {
  await page.goto("/")
  const legend = page.getByRole("figure", { name: data.metric.hansen, exact: true })
  const resize = page.getByRole("separator", { name: map.legend.resize })
  await expect(legend).toBeVisible()
  await resize.focus()
  await page.keyboard.press("End")
  await expect(resize).toHaveAttribute("aria-valuenow", "480")
  await page.getByRole("button", { name: map.legend.collapse }).hover()
  await page.waitForTimeout(700)
  await expect(page.getByRole("tooltip")).toHaveCount(0)
  await page.getByRole("button", { name: map.legend.collapse }).click()
  const open = page.getByRole("button", { name: map.legend.open })
  await expect(open).toBeFocused()
  await expect(legend).toHaveCount(0)
  await open.hover()
  await page.waitForTimeout(700)
  await expect(page.getByRole("tooltip")).toHaveCount(0)
  const shape = await open.boundingBox()
  expect(shape?.width).toBe(48)
  expect(shape?.height).toBe(48)
  await page.reload()
  await expect(open).toBeVisible()
  await expect(legend).toHaveCount(0)
  await open.press("Enter")
  await expect(legend).toBeVisible()
  await expect(page.getByRole("button", { name: map.legend.collapse })).toBeFocused()
  await expect(resize).toHaveAttribute("aria-valuenow", "480")
  await expect.poll(async () => (await legend.boundingBox())?.width).toBe(480)
  const motion = await legend.evaluate((element) => element.getAnimations().length)
  expect(motion).toBe(0)
})

test("legend resizes in either direction with pointer and keyboard", async ({ page }) => {
  await page.goto("/")
  const legend = page.getByRole("figure", { name: data.metric.hansen, exact: true })
  const resize = page.getByRole("separator", { name: map.legend.resize })
  await expect(legend).toBeVisible()
  await expect(resize).toHaveAttribute("aria-valuenow", "320")
  const box = await resize.boundingBox()
  if (!box) throw new Error("Legend resize control is missing")
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2)
  await page.mouse.down()
  await page.mouse.move(box.x + box.width / 2 + 100, box.y + box.height / 2, { steps: 5 })
  await page.mouse.up()
  await expect.poll(async () => (await legend.boundingBox())?.width).toBe(420)
  await resize.focus()
  await page.keyboard.press("Home")
  await expect(resize).toHaveAttribute("aria-valuenow", "240")
  await page.keyboard.press("ArrowRight")
  await expect(resize).toHaveAttribute("aria-valuenow", "256")
  await page.keyboard.press("ArrowLeft")
  await expect(resize).toHaveAttribute("aria-valuenow", "240")
  await page.keyboard.press("ArrowLeft")
  await expect(resize).toHaveAttribute("aria-valuenow", "240")
  await resize.dblclick()
  await expect(resize).toHaveAttribute("aria-valuenow", "320")
  const sidebar = page.getByRole("separator", { name: map.panelResize })
  await sidebar.focus()
  await page.keyboard.press("Home")
  await page.keyboard.press("ArrowLeft")
  await expect(sidebar).toHaveAttribute("aria-valuenow", "336")
  await expect.poll(async () => (await legend.boundingBox())?.width).toBe(320)
})

test("legend remains operable with reduced motion and blocked storage", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" })
  await page.addInitScript(() => {
    Storage.prototype.setItem = () => {
      throw new DOMException("Storage unavailable", "SecurityError")
    }
  })
  await page.goto("/")
  await page.getByRole("button", { name: map.legend.collapse }).click()
  const open = page.getByRole("button", { name: map.legend.open })
  await expect(open).toBeVisible()
  await open.click()
  const legend = page.getByRole("figure", { name: data.metric.hansen, exact: true })
  await expect(legend).toBeVisible()
  const resize = page.getByRole("separator", { name: map.legend.resize })
  await resize.focus()
  await page.keyboard.press("End")
  await expect(resize).toHaveAttribute("aria-valuenow", "480")
  const corner = page.getByRole("button", { name: map.legend.resizeBoth })
  const before = await legend.boundingBox()
  if (!before) throw new Error("Legend is missing")
  await corner.focus()
  await page.keyboard.press("ArrowUp")
  await expect
    .poll(async () => (await legend.boundingBox())?.height)
    .toBe(Math.round(before.height) + 16)
})

test("legend grows and shrinks diagonally while its lower-left corner stays fixed", async ({
  page,
}) => {
  await page.goto("/")
  const legend = page.getByRole("figure", { name: data.metric.hansen, exact: true })
  const corner = page.getByRole("button", { name: map.legend.resizeBoth })
  await expect(legend).toBeVisible()
  await expect(corner.locator("svg")).toHaveCount(0)
  await corner.hover()
  await expect(corner).toHaveCSS("cursor", "nesw-resize")
  const before = await legend.boundingBox()
  const handle = await corner.boundingBox()
  if (!before || !handle) throw new Error("Legend resize control is missing")
  expect(handle.x).toBeGreaterThan(before.x + before.width - 12)
  expect(handle.y).toBeLessThan(before.y)
  await page.mouse.move(handle.x + handle.width / 2, handle.y + handle.height / 2)
  await page.mouse.down()
  await page.mouse.move(handle.x + handle.width / 2 + 100, handle.y + handle.height / 2 - 120, {
    steps: 8,
  })
  await page.mouse.up()
  await expect.poll(async () => (await legend.boundingBox())?.width).toBe(420)
  await expect
    .poll(async () => (await legend.boundingBox())?.height)
    .toBe(Math.round(before.height) + 120)
  await expect.poll(async () => (await legend.boundingBox())?.x).toBe(before.x)
  await expect
    .poll(async () => {
      const box = await legend.boundingBox()
      return box ? box.y + box.height : null
    })
    .toBe(before.y + before.height)
  const grownHandle = await corner.boundingBox()
  if (!grownHandle) throw new Error("Legend resize control is missing")
  await page.mouse.move(
    grownHandle.x + grownHandle.width / 2,
    grownHandle.y + grownHandle.height / 2,
  )
  await page.mouse.down()
  await page.mouse.move(
    grownHandle.x + grownHandle.width / 2 - 180,
    grownHandle.y + grownHandle.height / 2 + 250,
    { steps: 8 },
  )
  await page.mouse.up()
  await expect.poll(async () => (await legend.boundingBox())?.width).toBe(240)
  await expect.poll(async () => (await legend.boundingBox())?.height).toBe(160)
  const scrollable = () =>
    legend.evaluate((element) =>
      [...element.querySelectorAll("div")].some(
        (node) =>
          getComputedStyle(node).overflowY === "auto" && node.scrollHeight > node.clientHeight,
      ),
    )
  await expect.poll(scrollable).toBe(true)
  await page.getByRole("button", { name: map.legend.collapse }).click()
  await expect(legend).toHaveCount(0)
  await page.reload()
  await page.getByRole("button", { name: map.legend.open }).press("Enter")
  await expect.poll(async () => (await legend.boundingBox())?.width).toBe(240)
  await expect.poll(async () => (await legend.boundingBox())?.height).toBe(160)
})

test("legend corner supports keyboard resizing, cancellation and automatic size reset", async ({
  page,
}) => {
  await page.goto("/")
  const legend = page.getByRole("figure", { name: data.metric.hansen, exact: true })
  const corner = page.getByRole("button", { name: map.legend.resizeBoth })
  await expect(legend).toBeVisible()
  const before = await legend.boundingBox()
  const handle = await corner.boundingBox()
  if (!before || !handle) throw new Error("Legend resize control is missing")
  await page.mouse.move(handle.x + handle.width / 2, handle.y + handle.height / 2)
  await page.mouse.down()
  await page.mouse.move(handle.x + handle.width / 2 + 100, handle.y + handle.height / 2 - 100, {
    steps: 5,
  })
  await expect
    .poll(async () => (await legend.boundingBox())?.height)
    .toBe(Math.round(before.height) + 100)
  await page.keyboard.press("Escape")
  await page.mouse.up()
  await expect.poll(async () => (await legend.boundingBox())?.height).toBe(before.height)
  await expect.poll(async () => (await legend.boundingBox())?.width).toBe(before.width)
  await corner.focus()
  await page.keyboard.press("ArrowRight")
  await page.keyboard.press("Shift+ArrowUp")
  await expect.poll(async () => (await legend.boundingBox())?.width).toBe(before.width + 16)
  await expect
    .poll(async () => (await legend.boundingBox())?.height)
    .toBe(Math.round(before.height) + 64)
  await page.keyboard.press("ArrowDown")
  await expect
    .poll(async () => (await legend.boundingBox())?.height)
    .toBe(Math.round(before.height) + 48)
  await page.keyboard.press("Home")
  await expect.poll(async () => (await legend.boundingBox())?.width).toBe(before.width)
  await expect.poll(async () => (await legend.boundingBox())?.height).toBe(before.height)
})

test("legend corner clamps dimensions to the viewport and resets on double click", async ({
  page,
}) => {
  await page.goto("/")
  const legend = page.getByRole("figure", { name: data.metric.hansen, exact: true })
  const corner = page.getByRole("button", { name: map.legend.resizeBoth })
  await expect(legend).toBeVisible()
  const handle = await corner.boundingBox()
  if (!handle) throw new Error("Legend resize control is missing")
  await page.mouse.move(handle.x + handle.width / 2, handle.y + handle.height / 2)
  await page.mouse.down()
  await page.mouse.move(1400, 0, { steps: 8 })
  await page.mouse.up()
  await expect.poll(async () => (await legend.boundingBox())?.width).toBe(480)
  await page.setViewportSize({ width: 1200, height: 720 })
  await expect.poll(async () => (await legend.boundingBox())?.height).toBe(528)
  await expect.poll(async () => (await legend.boundingBox())?.y).toBeGreaterThan(64)
  await corner.dblclick()
  await expect.poll(async () => (await legend.boundingBox())?.width).toBe(320)
  await expect.poll(async () => (await legend.boundingBox())?.height).toBeLessThan(400)
})
