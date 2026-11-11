const { chromium } = require('../../frontend/node_modules/@playwright/test');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.addInitScript(() => {
    const session = { version: 1, id: 'sequence-check', createdAt: Date.now(), updatedAt: Date.now(), draft: '', status: 'done', error: null,
      messages: [{ id: 'answer', role: 'assistant', content: 'Первый абзац ответа.\n\n**Второй абзац ответа.**', complete: true, steps: [], charts: [], mapCommands: [], tables: [{ id: 'table', title: 'sensitivity', columns: [{key: 'name', format: 'text'}], rows: [{name: 'TEMPLATE_SHOULD_NOT_RENDER'}], total: 1, truncated: false, source: 'model:test' }] }] };
    localStorage.setItem('plexus.chat.session.v1.sequence-check', JSON.stringify(session));
    localStorage.setItem('plexus.chat.active.v1', 'sequence-check');
  });
  await page.goto('http://127.0.0.1:5187/?region=18000000&season=road&panel=chat');
  await page.getByText('Второй абзац ответа.', { exact: true }).waitFor();
  if (await page.getByText('TEMPLATE_SHOULD_NOT_RENDER').count()) throw Error('Generated prose remains');
  await page.screenshot({ path: 'work/chat-sequential/desktop.png' });
  console.log(JSON.stringify({ errors, templateAbsent: true }));
  await browser.close();
  if (errors.length) process.exitCode = 1;
})();
