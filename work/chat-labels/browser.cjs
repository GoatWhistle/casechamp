const { chromium } = require('../../frontend/node_modules/@playwright/test');
const fs=require('node:fs');
(async()=>{
 const browser=await chromium.launch({headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 const jobs=JSON.parse(fs.readFileSync('/tmp/chat-stress-jobs.json','utf8')).slice(0,2).reverse();
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.addInitScript(jobs=>{
 const session={version:1,id:'labels-check',createdAt:Date.now(),updatedAt:Date.now(),draft:'',status:'done',error:null,messages:[{id:'answer',role:'assistant',content:'Сравнение сохранённых перекрытий.',complete:true,reviewPending:false,steps:[],tables:[],charts:[],mapCommands:[],stressTests:jobs}]};
 localStorage.setItem('plexus.chat.session.v1.labels-check',JSON.stringify(session));localStorage.setItem('plexus.chat.active.v1','labels-check');
 },jobs);
 await page.route('**/api/v1/chat/**',route=>{errors.push('Unexpected model request');return route.abort();});
 await page.goto('http://127.0.0.1:5187/?region=18000000&panel=chat');
 await page.getByText('Перекрытие М-10',{exact:true}).waitFor();
 await page.getByText(/Перекрытие М-10 \+ М-11/).waitFor();
 await page.screenshot({path:'work/chat-labels/desktop.png'});
 console.log(JSON.stringify({errors,labels:await page.locator('[data-calculation-run] strong').allTextContents()}));
 await browser.close();if(errors.length)process.exitCode=1;
})();
