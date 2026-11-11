const { chromium }=require('../../frontend/node_modules/@playwright/test');
(async()=>{
 const browser=await chromium.launch({headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.addInitScript(()=>{
 const session={version:1,id:'compact-check',createdAt:Date.now(),updatedAt:Date.now(),draft:'',status:'done',error:null,messages:[{id:'answer',role:'assistant',content:'**Индекс доступности М-10**\n\nРезультат расчёта и его интерпретация.',complete:true,steps:['calculate_scenario','reading','writing','connecting','queued','done'],tables:[],charts:[],mapCommands:[{action:'focus',region_ids:['18000000']}]}]};
 localStorage.setItem('plexus.chat.session.v1.compact-check',JSON.stringify(session));localStorage.setItem('plexus.chat.active.v1','compact-check');
 });
 await page.goto('http://127.0.0.1:5187/?region=18000000&panel=chat');
 const actions=page.getByRole('button',{name:'Действия: 6'});
 await actions.waitFor();
 await page.screenshot({path:'work/chat-compact/desktop.png'});
 await actions.click();
 if(await actions.getAttribute('aria-expanded')!=='true')throw Error('Actions did not expand');
 console.log(JSON.stringify({errors,expanded:true}));
 await browser.close();if(errors.length)process.exitCode=1;
})();
