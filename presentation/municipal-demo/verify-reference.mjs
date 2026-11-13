import {chromium} from '../../frontend/node_modules/@playwright/test/index.mjs';
import {writeFile,mkdir} from 'node:fs/promises';
const browser=await chromium.launch();
const page=await browser.newPage({viewport:{width:1440,height:810}});
const errors=[],requests=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url()))requests.push(r.url())});
await mkdir(new URL('./reference-shots/',import.meta.url),{recursive:true});
await page.goto(new URL('../plexus-deck.html',import.meta.url).href+'?static#1');
await page.waitForSelector('html[data-ready="true"]',{timeout:90000});
const checks=[];
for(const id of ['1','2.1','3','3.2','4','5.1','6','7','8.1','9']){
 await page.evaluate(async id=>{await window.deck.go(window.deck.ids().indexOf(id),true)},id);
 await page.waitForTimeout(250);
 await page.screenshot({path:new URL('./reference-shots/'+id+'.png',import.meta.url).pathname});
 const state=await page.evaluate(()=>({text:document.body.innerText,map:!!window.__plexusDemoMap,chat:!!document.querySelector('aside textarea')}));
 checks.push({id,map:state.map,chat:state.chat,waiting:state.text.includes('Подключаюсь…')});console.log(id,checks.at(-1));
}
await writeFile(new URL('./reference-validation.json',import.meta.url),JSON.stringify({errors,requests,checks},null,2));
await browser.close();if(errors.length||requests.length||checks.some(c=>c.waiting))throw Error(JSON.stringify({errors,requests,checks}));
