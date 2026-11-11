import fs from 'node:fs/promises'
import { createRequire } from 'node:module'
const require = createRequire(new URL('../../frontend/package.json', import.meta.url))
const AxeBuilder = require('@axe-core/playwright').default
import { chromium } from '../../frontend/node_modules/playwright/index.mjs'

const events = JSON.parse(await fs.readFile(new URL('./events.json', import.meta.url), 'utf8'))
const copy = JSON.parse(await fs.readFile(new URL('../../frontend/src/shared/i18n/locales/ru/chat.json', import.meta.url), 'utf8'))
const browser = await chromium.launch({ headless: true })
const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } })
const page = await context.newPage()
const errors = []
page.on('pageerror', e => errors.push(e.message))
await page.route('**/api/v1/chat', route => route.fulfill({
    status: 200, contentType: 'application/x-ndjson',
    body: [...events, { type: 'done', text: '', code: '' }].map(e => JSON.stringify(e)).join('\n') + '\n',
}))
await page.goto('http://127.0.0.1:5187/')
await page.getByRole('textbox', { name: copy.prompt, exact: true }).fill('Связанность четырёх населённых пунктов до и после закрытия дороги')
await page.getByRole('button', { name: copy.send, exact: true }).click()
await page.getByRole('heading', { name: copy.tables.connectivity, exact: true }).waitFor()
await page.getByRole('region', { name: copy.history, exact: true }).evaluate(node => node.scrollTop = 0)
await page.screenshot({ path: 'work/settlement-connectivity/desktop-1440.png' })
const pairs = page.getByRole('region', { name: copy.tables.connectivity, exact: true })
const geometry = await pairs.evaluate(node => ({ width: node.clientWidth, scroll: node.scrollWidth, cellHeight: node.querySelector('td').getBoundingClientRect().height }))
if (geometry.scroll <= geometry.width || geometry.cellHeight > 100) throw Error('Table does not preserve readable horizontal layout')
await pairs.evaluate(node => node.scrollLeft = node.scrollWidth)
await page.getByRole('button', { name: copy.window.expand, exact: true }).click()
await page.getByRole('region', { name: copy.history, exact: true }).evaluate(node => node.scrollTop = 0)
await page.screenshot({ path: 'work/settlement-connectivity/expanded-1440.png' })
if (await page.getByText(copy.routeStatus.unreachable, { exact: true }).count() !== 3) throw Error('Missing disconnected statuses')
await page.reload()
await page.getByRole('heading', { name: copy.tables.connectivity, exact: true }).waitFor()
if (await page.getByText(copy.routeStatus.unreachable, { exact: true }).count() !== 3) throw Error('History lost connectivity results')
await page.screenshot({ path: 'work/settlement-connectivity/history-1440.png' })
const axe = await new AxeBuilder({ page }).analyze()
const checks = { errors, tables: await page.getByRole('table').count(), history_restored: true, geometry, axe: axe.violations }
await fs.writeFile('work/settlement-connectivity/browser-checks.json', JSON.stringify(checks, null, 2))
console.log(JSON.stringify(checks))
if (axe.violations.length) throw Error('Accessibility violations')
await browser.close()
if (errors.length) throw Error(errors.join('\n'))
