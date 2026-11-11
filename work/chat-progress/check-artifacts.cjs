const { chromium } = require('../../frontend/node_modules/playwright')
const fs = require('node:fs')
const result = JSON.parse(fs.readFileSync('work/chat-debug/pair-validation.json', 'utf8'))
const columns = (keys, format) => keys.map(key => ({ key, format }))
const tables = [
  { id: 'summary', title: 'connectivity_summary', columns: columns(['score_before', 'score_after', 'delta'], 'number'), rows: [{ id: 'summary', ...Object.fromEntries(['score_before', 'score_after', 'delta', 'unbound_pairs', 'disconnected_pairs'].map(key => [key, result[key]])) }], total: 1, truncated: false, source: 'model:selected-settlements-road-v1' },
  { id: 'pairs', title: 'connectivity', columns: [...columns(['origin', 'destination'], 'text'), ...columns(['hours_before', 'hours_after', 'score_before', 'score_after'], 'number'), ...columns(['status_before', 'status_after'], 'text')], rows: result.pairs.map(pair => ({ id: `${pair.origin.id}:${pair.destination.id}`, origin: `${pair.origin.name}, ${pair.origin.region}`, destination: `${pair.destination.name}, ${pair.destination.region}`, hours_before: pair.before.hours, hours_after: pair.after.hours, status_before: pair.before.status, status_after: pair.after.status, score_before: pair.score_before, score_after: pair.score_after, delta: pair.delta })), total: 1, truncated: false, source: 'model:selected-settlements-road-v1' }
]
;(async () => {
  const browser = await chromium.launch({ headless: true })
  try {
    for (const variant of ['saved', 'missing']) {
      const data = structuredClone(tables)
      if (variant === 'missing') {
        Object.assign(data[0].rows[0], { score_before: null, score_after: null, delta: null, unbound_pairs: 1 })
        Object.assign(data[1].rows[0], { score_before: null, score_after: null, delta: null, hours_before: null, hours_after: null, status_before: 'unbound', status_after: 'unbound' })
      }
      const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' })
      const page = await context.newPage()
      const errors = []
      page.on('pageerror', e => errors.push(e.message))
      await page.route('**/api/v1/chat**', route => route.abort())
      await page.addInitScript(({ data }) => {
        const id = 'artifact-preview'
        localStorage.setItem('plexus.chat.active.v1', id)
        localStorage.setItem(`plexus.chat.session.v1.${id}`, JSON.stringify({ version: 1, id, createdAt: Date.now(), updatedAt: Date.now(), draft: '', status: 'done', error: null, messages: [{ id: 'answer', role: 'assistant', complete: true, reviewPending: false, content: '', steps: [], tables: data, charts: [], mapCommands: [] }] }))
      }, { data })
      await page.goto('http://127.0.0.1:5187/')
      const answer = page.locator('article[data-role="assistant"]').first()
      await answer.getByRole('heading').waitFor()
      const content = await answer.innerText()
      const frames = await answer.locator('*').evaluateAll(nodes => nodes.filter(node => { const style = getComputedStyle(node); return parseFloat(style.borderTopWidth) > 0 && style.borderTopStyle !== 'none' }).map(node => node.tagName))
      if (await answer.getByRole('table').count() || frames.length || errors.length) throw new Error(JSON.stringify({ frames, errors }))
      if (variant === 'saved' && (!content.includes('8,06') || !content.includes('13,90'))) throw new Error(content)
      if (content.includes('Санкт-Петербург, Санкт-Петербург')) throw new Error('Repeated region')
      await page.screenshot({ path: `work/chat-progress/artifact-${variant}-1440.png` })
      await answer.screenshot({ path: `work/chat-progress/artifact-${variant}-message.png` })
      console.log(JSON.stringify({ variant, content, frames, errors }))
      await context.close()
    }
  } finally { await browser.close() }
})().catch(error => { console.error(error); process.exitCode = 1 })
