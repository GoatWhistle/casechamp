const { chromium }=require('/Users/andreykuronskin/keys_champ/frontend/node_modules/@playwright/test');
(async()=>{const browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:1440,height:1000}});await page.goto('http://127.0.0.1:5187/?region=18000000');await page.waitForFunction(()=>[...document.querySelectorAll('[data-road-segments]')].some(e=>Number(e.dataset.roadSegments)>0&&e.dataset.roadRendering==='false'),{},{timeout:60000});
const result=await page.evaluate(async()=>{
 const source=await (await fetch('/src/entities/region/osm-map/use-osm-map.ts')).text();const url=source.match(/from "([^"]*maplibre-gl[^"?]*\.js[^\"]*)"/)[1];const mod=await import(url);const MapClass=mod.Map??mod.default.Map;
 let queries=0,queryMs=0;const original=MapClass.prototype.queryRenderedFeatures;MapClass.prototype.queryRenderedFeatures=function(...args){const start=performance.now();queries++;try{return original.apply(this,args)}finally{queryMs+=performance.now()-start}};
 const canvas=document.querySelector('.maplibregl-canvas');const runs=[];
 for(let run=0;run<3;run++){queries=0;queryMs=0;const start=performance.now();for(let i=0;i<120;i++)canvas.dispatchEvent(new MouseEvent('mousemove',{bubbles:true,clientX:100+(i%40)*20,clientY:300+(i%10)*10}));await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));runs.push({elapsedMs:performance.now()-start,queries,queryMs});}
 MapClass.prototype.queryRenderedFeatures=original;return runs;
});console.log(JSON.stringify(result));await browser.close()})();
