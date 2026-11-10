import AxeBuilder from "@axe-core/playwright"
import { expect, test } from "@playwright/test"
import ru from "../src/shared/i18n/locales/ru/accessibility.json"

for (const width of [1440, 1920]) {
  test(`regional accessibility comparison at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 1100 })
    const errors: string[] = []
    page.on("pageerror", (error) => errors.push(error.message))
    await page.goto("/regions/18000000?season=summer")
    const panel = page.getByRole("region", { name: ru.title })
    await expect(panel.getByRole("table", { name: ru.title })).toBeVisible()
    await expect(panel.getByText(ru.scheduleMissing)).toBeVisible()
    const changed = page.waitForResponse(
      (response) => response.url().includes("accessibility?half_life=8") && response.ok(),
    )
    await panel.getByRole("radio", { name: ru.hours_many.replace("{{count}}", "8") }).check()
    await changed
    await expect(panel.getByText(ru.sensitivity)).toBeVisible()
    await expect(panel.getByRole("table", { name: ru.effects })).toBeVisible()
    await panel.scrollIntoViewIfNeeded()
    await panel.screenshot({ path: `../work/accessibility-model/comparison-${width}.png` })
    const accessibility = await new AxeBuilder({ page }).include("section").analyze()
    expect(accessibility.violations).toEqual([])
    expect(errors).toEqual([])
  })
}
