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
let requestNumber = 0
let followupHistory = ''
page.on('pageerror', e => errors.push(e.message))
await page.route('**/api/v1/chat', route => {
  requestNumber++
  if (requestNumber > 1) followupHistory = route.request().postData() ?? ''
  return route.fulfill({status: 200, contentType: 'application/x-ndjson',
    body: [...(requestNumber === 1 ? events : []), { type: 'done', text: '', code: '' }].map(e => JSON.stringify(e)).join('\n') + '\n'})
})
await page.goto('http://127.0.0.1:5187/')
await page.getByRole('textbox', { name: copy.prompt, exact: true }).fill('Закрой мост, перенеси среднюю нагрузку на объезды')
await page.getByRole('button', { name: copy.send, exact: true }).click()
await page.getByRole('heading', { name: copy.tables.connectivity, exact: true }).waitFor()
const note = page.getByText(/Сценарные допущения:/)
await note.waitFor()
if (!(await note.innerText()).includes('50')) throw Error('Missing traffic assumptions')
await page.getByRole('region', { name: copy.history, exact: true }).evaluate(node => node.scrollTop = 0)
await page.screenshot({ path: 'work/traffic-diversion/desktop-1440.png' })
const pairs = page.getByRole('region', { name: copy.tables.connectivity, exact: true })
await pairs.evaluate(node => node.scrollLeft = node.scrollWidth)
await page.getByRole('button', { name: copy.window.expand, exact: true }).click()
await page.getByRole('region', { name: copy.history, exact: true }).evaluate(node => node.scrollTop = 0)
await page.screenshot({ path: 'work/traffic-diversion/expanded-1440.png' })
if (await page.getByText(copy.columns.queuePcu, { exact: true }).count() !== 1) throw Error('Missing queue result')
await page.reload()
await page.getByRole('heading', { name: copy.tables.connectivity, exact: true }).waitFor()
await page.getByRole('textbox', { name: copy.prompt, exact: true }).fill('А экономически?')
await Promise.all([page.waitForResponse(response => response.url().endsWith('/api/v1/chat')),
  page.getByRole('button', { name: copy.send, exact: true }).click()])
const reference = events[0].table.rows[0].calculation_id
if (!followupHistory.includes(reference)) throw Error('Next turn lost saved reference')
const axe = await new AxeBuilder({ page }).analyze()
const checks = { errors, history_restored: true, reference_in_followup: reference, axe: axe.violations }
await fs.writeFile('work/traffic-diversion/browser-checks.json', JSON.stringify(checks, null, 2))
console.log(JSON.stringify(checks))
await browser.close()
if (errors.length || axe.violations.length) throw Error('Browser checks failed')
