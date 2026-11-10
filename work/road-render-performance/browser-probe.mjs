import { chromium } from '../../frontend/node_modules/playwright/index.mjs'
import { writeFile } from 'node:fs/promises'
import assert from 'node:assert/strict'

const base = process.env.PROBE_URL ?? 'http://127.0.0.1:5187'
const browser = await chromium.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' })
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
const profiler = await page.context().newCDPSession(page)
await profiler.send('Profiler.enable')
const errors = []
const roadRequests = []
page.context().on("request", request => { if(request.url().includes("/api/v1/road-graph")) { roadRequests.push(request.url()); console.log("ROAD REQUEST", request.url()) } })
page.context().on("response", response => { if(response.url().includes("/api/v1/road-graph")) console.log("ROAD RESPONSE", response.status()) })
page.on('pageerror', error => errors.push(error.message))
page.on('console', message => { if(message.type() === 'error') console.log('CONSOLE', message.text()) })
await page.addInitScript(() => {
  performance.setResourceTimingBufferSize(5000)
  window.__events = []
  window.__longTasks = []
  new PerformanceObserver(list => {
    window.__longTasks.push(...list.getEntries().map(e => ({ start: e.startTime, duration: e.duration })))
  }).observe({ type: 'longtask', buffered: true })
  window.__attachMap = map => {
    window.__map = map
    const log = (event, detail = {}) => window.__events.push({ event, time: performance.now(), ...detail })
    const addSource = map.addSource.bind(map)
    map.addSource = (id, options) => {
      log('addSource', { id, features: options.data?.features?.length })
      const result = addSource(id, options)
      const source = map.getSource(id)
      if (source.setData) {
        const setData = source.setData.bind(source)
        source.setData = data => {
          const start = performance.now()
          log('setData', { id, features: data?.features?.length })
          const result = setData(data)
          log('setDataReturn', { id, duration: performance.now() - start })
          Promise.resolve(result).then(() => log('setDataDone', { id }))
          return result
        }
      }
      return result
    }
    map.on('sourcedata', e => {
      if (e.isSourceLoaded && e.sourceId !== 'osm') log('sourceLoaded', { id: e.sourceId })
    })
    map.on('moveend', () => log('moveend', { zoom: map.getZoom() }))
  }
})
await page.route('**/src/entities/region/osm-map/use-osm-map.ts*', async route => {
  const response = await route.fetch()
  const body = await response.text()
  assert(body.includes('const map = new LibreMap(options);'))
  await route.fulfill({ response, body: body.replace('const map = new LibreMap(options);', 'const map = new LibreMap(options); window.__attachMap(map);') })
})
page.setDefaultTimeout(120000)
if (process.env.PROBE_PRODUCTION) {
  await page.route('**/assets/region-*.js', async route => {
    const response = await route.fetch()
    const body = await response.text()
    const match = body.match(/(let (\w+)=new \w+\(\{container:[\s\S]*?fadeDuration:[\s\S]*?\}\);)/)
    assert(match, 'Find production map constructor')
    await route.fulfill({ response, body: body.replace(match[1], `${match[1]}window.__attachMap(${match[2]});`) })
  })
}
const cases = []
async function capture(name, action, fromNavigation = false) {
  const start = fromNavigation ? 0 : await page.evaluate(() => performance.now())
  const requestStart = roadRequests.length
  await profiler.send('Profiler.start')
  await action()
  if (name !== 'pan20px') {
    await page.waitForFunction(start => window.__events?.some(e => e.time >= start && e.event === 'setData' && e.id.startsWith('road-graph-lines')), start)
    await page.waitForFunction(() => document.querySelector('[data-map-surface]')?.dataset.roadRendering === 'false')
  }
  await page.waitForFunction(() => window.__map && !window.__map.isMoving() && Object.keys(window.__map.getStyle().sources).filter(id => id.startsWith('road-graph-lines')).every(id => window.__map.isSourceLoaded(id)))
  await page.waitForTimeout(1500)
  const data = await page.evaluate(start => ({
    events: window.__events.filter(e => e.time >= start),
    longTasks: window.__longTasks.filter(e => e.start >= start),
    requests: performance.getEntriesByType('resource').filter(e => e.startTime >= start && e.name.includes('/api/')).map(e => ({ url: e.name.replace(location.origin, ''), start: e.startTime, ttfb: e.responseStart - e.startTime, duration: e.duration, bytes: e.decodedBodySize })),
    roads: document.querySelector('[data-map-surface]')?.dataset.roadSegments,
    transit: document.querySelector('[data-map-surface]')?.dataset.transitConnections,
  }), start)
  const { profile } = await profiler.send('Profiler.stop')
  await writeFile(`work/road-render-performance/${name}.cpuprofile`, JSON.stringify(profile))
  data.roadRequests = roadRequests.slice(requestStart)
  cases.push({ name, ...data })
  console.log(JSON.stringify({ name, roads: data.roads, transit: data.transit, longTasks: data.longTasks, roadRequests: data.roadRequests, requests: data.requests.filter(r => /road-graph|links/.test(r.url)) }))
}
try {
  await page.goto(base, { waitUntil: 'domcontentloaded' })
  await capture('country', async () => {}, true)
  await capture('regional-zoom7', () => page.evaluate(() => { window.__map.jumpTo({ center: [40.5, 55.5], zoom: 7 }); }))
  await capture('pan20px', () => page.evaluate(() => { window.__map.panBy([20, 0], { duration: 0 }); }))
  const picked = await page.evaluate(() => {
    const map = window.__map
    const layers = map.getStyle().layers.filter(layer => layer.id.startsWith('road-graph-lines')).map(layer => layer.id)
    for (const feature of map.queryRenderedFeatures([[200, 200], [850, 650]], { layers: layers.slice(1) })) {
      if (feature.geometry.type !== 'LineString') continue
      for (const coordinate of feature.geometry.coordinates) {
        const point = map.project(coordinate)
        if (point.x < 200 || point.x > 850 || point.y < 200 || point.y > 650) continue
        const top = map.queryRenderedFeatures(point, { layers })[0]
        if (top) return { x: point.x, y: point.y, way: top.properties.way_id }
      }
    }
  })
  assert(picked, 'Road in a later chunk is visible')
  const canvasBox = await page.locator('.maplibregl-canvas').boundingBox()
  await page.mouse.click(canvasBox.x + picked.x, canvasBox.y + picked.y)
  await page.waitForFunction(way => window.__map.getPaintProperty('road-graph-lines', 'line-width')[1][2][1].includes(way), picked.way)
  console.log('ROAD CLICK PASSED', picked.way)
  await page.goto(base + '/?region=87000000', { waitUntil: 'domcontentloaded' })
  await capture('komi', async () => {}, true)
  await page.screenshot({ path: 'work/road-render-performance/browser-current.png' })
} finally {
  console.log("FINAL STATE", await page.evaluate(() => ({dataset: {...document.querySelector("[data-map-surface]")?.dataset}, events: window.__events?.slice(-25), body: document.body.innerText.slice(-1800)})))
  await writeFile('work/road-render-performance/browser-current.json', JSON.stringify({ date: new Date().toISOString(), base, viewport: '1440x900', browser: browser.version(), errors, cases }, null, 2))
  await browser.close()
}
const pan = cases.find(c => c.name === 'pan20px')
assert.equal(pan.roadRequests.length, 0, 'Small pan must reuse loaded geometry')
assert.equal(pan.events.filter(e => e.event === 'setData' && e.id.startsWith('road-graph-lines')).length, 0)
assert.equal(errors.length, 0)
