import { chromium } from '../../frontend/node_modules/playwright/index.mjs'
import { writeFile } from 'node:fs/promises'
const browser = await chromium.launch({executablePath:'/home/ikhail_horokhorin/.cache/ms-playwright/chromium-1248/chrome-linux64/chrome'})
const context = await browser.newContext({viewport:{width:1440,height:900},deviceScaleFactor:2})
const page = await context.newPage()
const cdp = await context.newCDPSession(page)
await cdp.send('Emulation.setCPUThrottlingRate',{rate:6})
await page.goto('http://127.0.0.1:8080/',{waitUntil:'networkidle'})
await page.waitForTimeout(1000)
const map=page.locator('svg[role="img"]')
const box=await map.boundingBox()
const x=box.x+box.width*.5,y=box.y+box.height*.55
const before=await map.locator(':scope > g').getAttribute('style')
await page.mouse.move(x,y);await page.mouse.down();await page.mouse.move(x+140,y+70,{steps:15});await page.mouse.up()
const after=await map.locator(':scope > g').getAttribute('style')
console.log('HOME DRAG', {before,after,moved:before!==after})
await page.goto('http://127.0.0.1:8080/?region=11000000',{waitUntil:'networkidle'})
await page.waitForTimeout(3000)
await page.screenshot({path:'work/map-performance/arkhangelsk-before.png'})
console.log('ARK',await map.evaluate(svg=>{const p=svg.querySelector('[data-id="11000000"]');const b=p.getBBox();return {bbox:[b.x,b.y,b.width,b.height],matrix:svg.querySelector('g').style.transform,rect:p.getBoundingClientRect().toJSON()}}))
await page.mouse.move(x,y)
await browser.startTracing(page,{categories:['devtools.timeline','disabled-by-default-devtools.timeline','toplevel','benchmark']})
await page.evaluate(async()=>{
 const svg=document.querySelector('svg[role="img"]'),rect=svg.getBoundingClientRect()
 window.__deltas=[];let prev=performance.now()
 for(let i=0;i<180;i++){
  await new Promise(requestAnimationFrame);const now=performance.now();window.__deltas.push(now-prev);prev=now
  svg.dispatchEvent(new WheelEvent('wheel',{deltaY:i<90?-16:16,bubbles:true,cancelable:true,clientX:rect.x+rect.width*.5,clientY:rect.y+rect.height*.55}))
 }
})
await page.waitForTimeout(500)
const trace=JSON.parse((await browser.stopTracing()).toString()).traceEvents
const totals={};for(const e of trace)if(e.ph==='X'&&['Layout','Paint','RasterTask','UpdateLayoutTree','FunctionCall'].includes(e.name))totals[e.name]=(totals[e.name]??0)+e.dur/1000
const frames=await page.evaluate(()=>window.__deltas)
const result={homeDrag:before!==after,frames:frames.length,over50:frames.filter(t=>t>50).length,max:Math.max(...frames),totals}
console.log(JSON.stringify(result));await writeFile('work/map-performance/regression-before.json',JSON.stringify(result,null,2))
await browser.close()
