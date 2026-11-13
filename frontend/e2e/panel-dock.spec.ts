import { expect, test } from "@playwright/test"
import chat from "../src/shared/i18n/locales/ru/chat.json" with { type: "json" }
import map from "../src/shared/i18n/locales/ru/map.json" with { type: "json" }

test("collapses the side panel fully and keeps it collapsed after reload", async ({ page }) => {
  await page.goto("/map")
  const panel = page.getByRole("complementary", { name: chat.panelLabel })
  const collapse = page.getByRole("button", { name: map.dock.collapse })
  const expand = page.getByRole("button", { name: map.dock.expand })
  await expect(panel).toBeVisible()
  await collapse.click()
  await expect(panel).toBeHidden()
  await expect(expand).toBeVisible()
  await page.reload()
  await expect(expand).toBeVisible()
  await expect(panel).toBeHidden()
  await expand.click()
  await expect(panel).toBeVisible()
  await expect(collapse).toBeVisible()
})
