const { createRequire } = require('node:module')
const { readFile } = require('node:fs/promises')
const requireFrontend = createRequire(`${process.cwd()}/frontend/package.json`)
const { chromium } = requireFrontend('playwright')
const copy = requireFrontend('./src/shared/i18n/locales/ru/pilot.json')

async function main() {
  const browser = await chromium.launch()
  try {
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } })
    const blocked = []
    await context.route('**/*', async (route) => {
      const url = new URL(route.request().url())
      if (!['localhost', '127.0.0.1'].includes(url.hostname)) {
        blocked.push(url.href)
        await route.abort()
      } else {
        await route.continue()
      }
    })
    const page = await context.newPage()
    await page.goto('http://127.0.0.1:18090/map?region=93000000&season=summer')
    await page.getByRole('link', { name: copy.open, exact: true }).click()
    await page.getByRole('heading', { name: copy.title, exact: true }).waitFor()
    const frequency = page.getByRole('textbox', { name: copy.frequency, exact: true }).first()
    await frequency.fill('7')
    await page.getByRole('button', { name: copy.calculate, exact: true }).click()
    await page.getByText('14,24', { exact: true }).first().waitFor()
    const downloadEvent = page.waitForEvent('download')
    await page.getByRole('button', { name: copy.json, exact: true }).click()
    const download = await downloadEvent
    const result = JSON.parse(await readFile(await download.path(), 'utf8'))
    if (result.evaluation.changes[0].frequency_per_week !== 7) throw new Error('Unexpected export')
    await page.getByRole('button', { name: copy.reset, exact: true }).click()
    if (await frequency.inputValue() !== '2') throw new Error('Reset failed')
    console.log(JSON.stringify({ outcome: 'passed', scenario: 'map, pilot, seven flights, JSON export, reset', blockedExternalRequests: blocked }))
  } finally {
    await browser.close()
  }
}
main().catch((error) => { console.error(error); process.exit(1) })
