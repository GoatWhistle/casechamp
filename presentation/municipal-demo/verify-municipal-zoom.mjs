import {chromium} from '../../frontend/node_modules/@playwright/test/index.mjs';
const b=await chromium.launch();const p=await b.newPage({viewport:{width:1440,height:810}});const errors=[];p.on('pageerror',e=>errors.push(e.message));
await p.goto(new URL('../plexus-deck.html',import.meta.url).href+'?static#2.1');await p.waitForSelector('html[data-ready="true"]',{timeout:90000});
for(const id of ['2.1','4']){await p.evaluate(async id=>window.deck.go(window.deck.ids().indexOf(id),true),id);await p.screenshot({path:new URL('./reference-shots/municipal-'+id+'.png',import.meta.url).pathname});console.log(id,await p.evaluate(()=>window.__plexusDemoMap.getZoom()));}
await b.close();if(errors.length)throw Error(errors.join('\n'));
