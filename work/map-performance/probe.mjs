import { chromium } from '../../frontend/node_modules/playwright/index.mjs'
import { writeFile } from 'node:fs/promises'
const base = process.env.PROBE_URL ?? 'http://127.0.0.1:4173'
const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH ?? '/home/ikhail_horokhorin/.cache/ms-playwright/chromium-1248/chrome-linux64/chrome' })
const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 })
const page = await context.newPage()
const results = { date: new Date().toISOString(), base, browser: browser.version(), viewport: '1440x900', dpr: 2, cases: [] }
async function open(path) {
  await page.goto(base + path, { waitUntil: 'networkidle' })
  await page.waitForTimeout(2000)
}
async function measure(name, action) {
  await page.evaluate(() => {
    window.__frames = []; window.__long = []; window.__record = true
    let prev = performance.now()
    const frame = now => { window.__frames.push(now - prev); prev = now; if (window.__record) requestAnimationFrame(frame) }
    requestAnimationFrame(frame)
    window.__observer = new PerformanceObserver(list => window.__long.push(...list.getEntries().map(e => e.duration)))
    window.__observer.observe({ type: 'longtask' })
    window.__mutations = 0
    window.__mutationObserver = new MutationObserver(list => { window.__mutations += list.filter(m => m.target.matches('svg[role="img"] > g') && m.attributeName === 'style').length })
    window.__mutationObserver.observe(document.body, { attributes: true, subtree: true })
  })
  await browser.startTracing(page, { categories: ['devtools.timeline', 'disabled-by-default-devtools.timeline', 'toplevel'] })
  await action()
  await page.waitForTimeout(600)
  const trace = JSON.parse((await browser.stopTracing()).toString()).traceEvents
  const result = await page.evaluate(() => {
    window.__record = false; window.__observer.disconnect(); window.__mutationObserver.disconnect()
    const frames = window.__frames.slice(1).sort((a,b) => a-b)
    return { frameP95: frames[Math.floor(frames.length * .95)], framesOver50: frames.filter(x => x > 50).length, longTasks: window.__long, svgCommits: window.__mutations,
      scrollY, innerScroll: [...document.querySelectorAll('*')].filter(e => e.scrollTop > 0 && e !== document.scrollingElement).map(e => [e.className, e.scrollTop]) }
  })
  const timings = {}
  for (const event of trace) if (event.ph === 'X' && ['Layout','Paint','RasterTask','UpdateLayoutTree'].includes(event.name)) timings[event.name] = (timings[event.name] ?? 0) + event.dur / 1000
  results.cases.push({name, ...result, timings})
  console.log(JSON.stringify(results.cases.at(-1)))
}
await open('/')
results.prevented = await page.locator('svg[role="img"]').evaluate(svg => {
  const event = new WheelEvent('wheel', { deltaY: -20, ctrlKey: true, bubbles: true, cancelable: true })
  svg.dispatchEvent(event)
  return event.defaultPrevented
})
await open('/')
const box = await page.locator('svg[role="img"]').boundingBox()
const x = box.x + box.width * .55, y = box.y + box.height * .55
await page.mouse.move(x,y)
await measure('wheel 12 ticks', async () => { for(let i=0;i<12;i++){ await page.mouse.wheel(0,-100); await page.waitForTimeout(16) } })
await measure('drag 30 moves', async () => { await page.mouse.down(); for(let i=1;i<=30;i++){ await page.mouse.move(x+i*6,y+i*2); await page.waitForTimeout(16) } await page.mouse.up() })
await open('/')
await measure('hover 60 moves', async () => { for(let i=0;i<60;i++) { await page.mouse.move(box.x+box.width*(.2+i*.01),y); await page.waitForTimeout(16) } })
await open('/?region=04000000')
await page.mouse.move(x,y)
await measure('selected wheel 12 ticks', async () => { for(let i=0;i<12;i++){ await page.mouse.wheel(0,-100); await page.waitForTimeout(16) } })
for(const path of ['/regions','/seasons','/method','/sources','/regions/04000000']) {
  await open(path)
  await page.mouse.move(1440*.35,600)
  await measure(`scroll ${path}`, async () => { for(let i=0;i<20;i++){ await page.mouse.wheel(0,120); await page.waitForTimeout(16) } })
}
await open('/')
for(const path of ['/regions','/seasons','/method','/sources','/']) {
  await measure(`navigation ${path}`, async () => { await page.locator(`header nav a[href="${path}"]`).click(); await page.waitForURL(base + path); await page.waitForLoadState('networkidle') })
}
await writeFile(new URL(process.argv[2] ?? 'result.json', import.meta.url), JSON.stringify(results,null,2)+'\n')
await browser.close()
