import { mkdirSync, readFileSync } from "node:fs"
import { join, resolve } from "node:path"
import { fileURLToPath } from "node:url"
import { chromium } from "@playwright/test"

interface Words {
  readonly summary: string
  readonly zoomOut: string
}

const REGION = "28000000"
const ZOOM_OUT_STEPS = 2
const SETTLE_MS = 15_000
const WARMUP_MS = 120_000

const frontendRoot = resolve(fileURLToPath(new URL("..", import.meta.url)))
const repoRoot = resolve(frontendRoot, "..")
const outDir = join(repoRoot, "docs", "readme")
const base = (process.env.APP_URL ?? "http://127.0.0.1:5187").replace(/\/$/, "")

function words(): Words {
  const locales = join(frontendRoot, "src", "shared", "i18n", "locales", "ru")
  const chat = JSON.parse(readFileSync(join(locales, "chat.json"), "utf8")) as { summary: string }
  const map = JSON.parse(readFileSync(join(locales, "map.json"), "utf8")) as { zoomOut: string }
  return { summary: chat.summary, zoomOut: map.zoomOut }
}

const text = words()
mkdirSync(outDir, { recursive: true })
const browser = await chromium.launch()
const page = await browser.newPage({
  viewport: { width: 1440, height: 900 },
  deviceScaleFactor: 2,
  reducedMotion: "reduce",
})
const path = `/?region=${REGION}&season=summer&network_mode=road`
const response = await page.goto(`${base}${path}`)
if (response === null || !response.ok()) throw new Error(`${base}${path} did not open`)
const summary = page.getByRole("tab", { name: text.summary })
await summary.waitFor({ timeout: WARMUP_MS })
await summary.click()
await page.getByRole("tabpanel", { name: text.summary }).waitFor({ timeout: WARMUP_MS })
const zoomOut = page.getByRole("button", { name: text.zoomOut, exact: true })
for (let step = 0; step < ZOOM_OUT_STEPS; step += 1) await zoomOut.click()
await page.waitForTimeout(SETTLE_MS)
await page.screenshot({ path: join(outDir, "hero-map.jpg"), type: "jpeg", quality: 88 })
await browser.close()
process.stdout.write(`docs/readme/hero-map.jpg from ${base}${path}\n`)
