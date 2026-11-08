import { chromium } from '../../frontend/node_modules/playwright/index.mjs'
import AxeBuilder from '../../frontend/node_modules/@axe-core/playwright/dist/index.mjs'
import { writeFile } from 'node:fs/promises'
const browser = await chromium.launch({ executablePath: '/home/ikhail_horokhorin/.cache/ms-playwright/chromium-1248/chrome-linux64/chrome' })
const evidence = []
for (const width of [375, 1440]) {
  const context = await browser.newContext({ viewport: {width, height: 900} })
  const page = await context.newPage()
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  for (const path of ['/', '/?region=04000000', '/regions', '/seasons', '/method', '/sources']) {
    await page.goto('http://127.0.0.1:4173' + path, {waitUntil:'networkidle'})
    await page.waitForTimeout(2000)
    if (['/', '/?region=04000000', '/regions'].includes(path)) {
      await page.screenshot({path:`work/map-performance/${path.includes('?') ? 'selected' : path === '/' ? 'map' : 'regions'}-${width}.png`})
    }
    const violations = (await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze()).violations.map(v => ({id:v.id, impact:v.impact, targets:v.nodes.map(n=>n.target)}))
    evidence.push({width,path,violations,overflow: await page.evaluate(()=>document.documentElement.scrollWidth > innerWidth), errors:[...errors]})
  }
  await context.close()
}
await writeFile('work/map-performance/visual.json', JSON.stringify(evidence,null,2)+'\n')
await browser.close()
