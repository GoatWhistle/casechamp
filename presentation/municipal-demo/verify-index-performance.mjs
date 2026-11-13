import {chromium} from '../../frontend/node_modules/@playwright/test/index.mjs';
import {writeFile} from 'node:fs/promises';
const b=await chromium.launch();const results=[];
for(const [label,url] of [['before','file:///tmp/plexus-before-perf.html'],['after',new URL('../plexus-deck.html',import.meta.url).href]]){
 const p=await b.newPage({viewport:{width:1440,height:810}});await p.goto(url+'?noauto#1');await p.waitForSelector('html[data-ready="true"]',{timeout:90000});
 const result=await p.evaluate(async()=>{const times=[];let previous=performance.now(),active=true;function frame(now){if(now-start<3900)times.push(now-previous);previous=now;if(active)requestAnimationFrame(frame)}requestAnimationFrame(frame);const start=performance.now();await window.deck.go(window.deck.ids().indexOf('3.1'),true);active=false;return {duration:performance.now()-start,frames:times.length,over33:times.filter(t=>t>33).length,p95:times.sort((a,b)=>a-b)[Math.floor(times.length*.95)]}});results.push({label,...result});console.log(label,result);await p.screenshot({path:new URL('./reference-shots/index-'+label+'.png',import.meta.url).pathname});await p.close();
}
await writeFile(new URL('./index-performance.json',import.meta.url),JSON.stringify(results,null,2));await b.close();
