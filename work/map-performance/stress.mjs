import { chromium } from '../../frontend/node_modules/playwright/index.mjs'
import { writeFile } from 'node:fs/promises'
const url=process.argv[2] ?? 'http://localhost:4173'
const browser=await chromium.launch({executablePath:'/home/ikhail_horokhorin/.cache/ms-playwright/chromium-1248/chrome-linux64/chrome'})
const context=await browser.newContext({viewport:{width:1440,height:900},deviceScaleFactor:2})
const page=await context.newPage();const cdp=await context.newCDPSession(page)
await cdp.send('Emulation.setCPUThrottlingRate',{rate:6})
const out={date:new Date().toISOString(),url,browser:browser.version(),cpu:6,dpr:2,cases:[]}
await page.goto(url+'/?region=11000000',{waitUntil:'networkidle'});await page.waitForTimeout(1200)
const selector='[data-map-surface],svg[role="img"]'
async function measure(name,action){
 await browser.startTracing(page,{categories:['devtools.timeline','disabled-by-default-devtools.timeline','toplevel','benchmark']})
 await page.evaluate(()=>{window.__frames=[];window.__running=true;let prev=performance.now();function frame(now){window.__frames.push(now-prev);prev=now;if(window.__running)requestAnimationFrame(frame)}requestAnimationFrame(frame)})
 await action();await page.waitForTimeout(250)
 const result=await page.evaluate(()=>{window.__running=false;const frames=window.__frames.slice(1).sort((a,b)=>a-b);return {frames:frames.length,over50:frames.filter(f=>f>50).length,p95:frames[Math.floor(frames.length*.95)],max:Math.max(...frames)}})
 const events=JSON.parse((await browser.stopTracing()).toString()).traceEvents
 const times={};for(const e of events)if(e.ph==='X'&&['RasterTask','Layout','Paint','UpdateLayoutTree','FunctionCall'].includes(e.name))times[e.name]=(times[e.name]??0)+e.dur/1000

 out.cases.push({name,...result,times});console.log(out.cases.at(-1))
}
await measure('180 wheel events to max zoom and back',()=>page.locator(selector).first().evaluate(async element=>{
 const rect=element.getBoundingClientRect()
 for(let i=0;i<180;i++){await new Promise(requestAnimationFrame);element.dispatchEvent(new WheelEvent('wheel',{deltaY:i<90?-16:16,bubbles:true,cancelable:true,clientX:rect.x+rect.width*.5,clientY:rect.y+rect.height*.55}))}
}))
await measure('90 drag events at selected region',async()=>{
 const box=await page.locator(selector).first().boundingBox();const x=box.x+box.width/2,y=box.y+box.height*.55
 await page.mouse.move(x,y);await page.mouse.down()
 for(let i=0;i<90;i++)await page.mouse.move(x+Math.sin(i/15)*250,y+Math.cos(i/15)*120)
 await page.mouse.up()
})
await measure('hover across region boundaries',async()=>{
 const box=await page.locator(selector).first().boundingBox()
 for(let i=0;i<90;i++)await page.mouse.move(box.x+box.width*(.1+.8*i/90),box.y+box.height*.6)
})
await writeFile(`work/map-performance/${process.argv[3]??'stress-after'}.json`,JSON.stringify(out,null,2)+'\n');await browser.close()
