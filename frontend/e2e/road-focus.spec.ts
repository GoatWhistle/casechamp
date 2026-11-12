import { expect, test } from "@playwright/test"
import chat from "../src/shared/i18n/locales/ru/chat.json" with { type: "json" }
import mapMessages from "../src/shared/i18n/locales/ru/map.json" with { type: "json" }

for (const width of [1440, 375])
  test(`saved road focus zooms to the checked section at ${width}px`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: 900 })
    const response = await page.request.get("/api/v1/road-analyses")
    expect(response.ok()).toBe(true)
    const analyses = await response.json()
    const analysis = analyses.find((row: { results: { candidate: { way_id: number } }[] }) =>
      row.results.some((result) => result.candidate.way_id === 201616290),
    )
    expect(analysis).toBeTruthy()
    const detailResponse = await page.request.get(
      `/api/v1/road-analyses/${analysis.id}/results/201616290`,
    )
    expect(detailResponse.ok()).toBe(true)
    const detail = await detailResponse.json()
    const road = {
      names: [detail.result.candidate.name],
      length_km: detail.result.candidate.length_km,
      lines: detail.lines,
    }
    await page.addInitScript((target) => {
      const session = {
        version: 1,
        id: "road-focus-check",
        title: target.names[0],
        createdAt: Date.now(),
        updatedAt: Date.now(),
        draft: "",
        status: "done",
        error: null,
        messages: [
          {
            id: "road-focus-reply",
            role: "assistant",
            content: target.names[0],
            complete: true,
            steps: [],
            tables: [],
            charts: [],
            mapCommands: [{ action: "focus_road", region_ids: [], road: target }],
          },
        ],
      }
      localStorage.setItem("plexus.chat.session.v1.road-focus-check", JSON.stringify(session))
      localStorage.setItem("plexus.chat.active.v1", session.id)
    }, road)
    await page.goto("/")
    const surface = page.locator("[data-map-surface]")
    await expect
      .poll(async () => Number(await surface.getAttribute("data-zoom")))
      .toBeGreaterThan(0)
    const action = page.getByRole("button", { name: chat.mapActions.focus_road, exact: true })
    await action.click()
    await expect(surface).toHaveAttribute("data-focus-road", road.names[0])
    await expect
      .poll(async () => Number(await surface.getAttribute("data-zoom")))
      .toBeGreaterThan(14)
    await page.screenshot({ path: info.outputPath(`road-focus-${width}.png`) })
    if (width === 1440) {
      await page.getByRole("button", { name: mapMessages.reset, exact: true }).click()
      await expect.poll(async () => Number(await surface.getAttribute("data-zoom"))).toBeLessThan(6)
      await action.click()
      await expect
        .poll(async () => Number(await surface.getAttribute("data-zoom")))
        .toBeGreaterThan(14)
    }
  })
