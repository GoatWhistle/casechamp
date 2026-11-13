import { expect, test } from "@playwright/test"
import chat from "../src/shared/i18n/locales/ru/chat.json" with { type: "json" }
import map from "../src/shared/i18n/locales/ru/map.json" with { type: "json" }

test.use({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true })

test("keeps the map above a half-height chat sheet and lets the chat take the full screen", async ({
  page,
}) => {
  await page.goto("/")
  const panel = page.getByRole("complementary", { name: chat.panelLabel })
  const surface = page.locator("[data-map-surface]")
  await expect(panel).toBeVisible()
  const mapBox = await surface.boundingBox()
  const panelBox = await panel.boundingBox()
  expect(mapBox?.y).toBe(0)
  expect((mapBox?.height ?? 0) + (panelBox?.height ?? 0)).toBeLessThanOrEqual(844)
  expect(panelBox?.y ?? 0).toBeGreaterThan(300)
  await expect(page.getByRole("textbox", { name: chat.prompt })).toBeInViewport()

  await page.getByRole("button", { name: map.dock.fill }).tap()
  await expect(page.getByRole("button", { name: map.dock.shrink })).toBeVisible()
  const coveredMap = surface.locator("xpath=ancestor::div[@inert]")
  await expect(coveredMap).toHaveCount(1)
  await page.getByRole("button", { name: map.dock.shrink }).tap()
  await expect(coveredMap).toHaveCount(0)
  await expect(page.getByRole("button", { name: map.zoomIn })).toBeInViewport()
})

test("hands focus to the launcher when the sheet hides and back when it opens", async ({
  page,
}) => {
  await page.goto("/")
  const panel = page.getByRole("complementary", { name: chat.panelLabel })
  await expect(panel).toBeVisible()
  await expect(page.getByRole("button", { name: map.zoomIn })).toBeVisible()
  await page.getByRole("button", { name: map.dock.collapse }).focus()
  await page.keyboard.press("Enter")
  const launcher = page.getByRole("button", { name: map.dock.expand })
  await expect(launcher).toBeFocused()
  await expect(panel).toBeHidden()
  await page.keyboard.press("Enter")
  await expect(panel).toBeVisible()
  await expect(page.getByRole("button", { name: map.dock.fill })).toBeFocused()
})

test("puts the chat beside the map on a phone held sideways", async ({ page }) => {
  await page.setViewportSize({ width: 844, height: 390 })
  await page.goto("/")
  const panel = page.getByRole("complementary", { name: chat.panelLabel })
  await expect(panel).toBeVisible()
  const mapBox = await page.locator("[data-map-surface]").boundingBox()
  const panelBox = await panel.boundingBox()
  expect(mapBox?.height).toBe(390)
  expect(mapBox?.width ?? 0).toBeGreaterThanOrEqual(422)
  expect(panelBox?.x ?? 0).toBeGreaterThanOrEqual(mapBox?.width ?? 0)
  await expect(page.getByRole("button", { name: map.zoomIn })).toBeInViewport()
})
