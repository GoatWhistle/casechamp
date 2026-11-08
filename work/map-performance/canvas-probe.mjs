import { chromium } from '../../frontend/node_modules/playwright/index.mjs'
const browser=await chromium.launch({executablePath:'/home/ikhail_horokhorin/.cache/ms-playwright/chromium-1248/chrome-linux64/chrome'})
const context=await browser.newContext({viewport:{width:1440,height:900},deviceScaleFactor:2})
const page=await context.newPage();await page.goto('http://localhost:8080/',{waitUntil:'networkidle'})
const cdp=await context.newCDPSession(page);await cdp.send('Emulation.setCPUThrottlingRate',{rate:6})
console.log(await page.evaluate(async()=>{
 const svg=document.querySelector('svg[role="img"]'),rect=svg.getBoundingClientRect(),dpr=devicePixelRatio
 const shapes=[...svg.querySelectorAll('path')].map(p=>({path:new Path2D(p.getAttribute('d')),fill:getComputedStyle(p).fill,box:p.getBBox()}))
 const canvas=document.createElement('canvas');canvas.width=rect.width*dpr;canvas.height=rect.height*dpr;canvas.style.width=rect.width+'px';canvas.style.height=rect.height+'px';svg.parentElement.replaceWith(canvas)
 const ctx=canvas.getContext('2d'),unit=Math.max(1000/rect.width,620/rect.height),times=[]
 for(let frame=0;frame<180;frame++){
  await new Promise(requestAnimationFrame);const start=performance.now();ctx.resetTransform();ctx.clearRect(0,0,canvas.width,canvas.height)
  const scale=1+frame/20;ctx.translate(canvas.width/2,canvas.height/2);ctx.scale(dpr*scale/unit,dpr*scale/unit);ctx.translate(-500,-310)
  ctx.lineWidth=unit/scale;ctx.strokeStyle='white'
  for(const s of shapes){ctx.fillStyle=s.fill;ctx.fill(s.path);ctx.stroke(s.path)}
  times.push(performance.now()-start)
 }
 times.sort((a,b)=>a-b);return {median:times[90],p95:times[171],max:times[179],dimensions:[canvas.width,canvas.height]}
}));await browser.close()
