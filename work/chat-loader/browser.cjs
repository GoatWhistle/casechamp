const { chromium } = require('../../frontend/node_modules/@playwright/test');
(async () => {
  const browser = await chromium.launch({headless:true});
  const page = await browser.newPage({viewport:{width:1440,height:1000}});
  const errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  const jobs=[
    {id:'loader-one',stage:'routes',status:'running',completed:116,total:180},
    {id:'loader-two',stage:'completed',status:'completed',completed:180,total:180},
  ].map(job=>({...job,version:'test',way_ids:[1],points:155264,unbound_points:0,preexisting_isolated_points:0,newly_isolated_points:0,regions:[]}));
  await page.route('**/api/v1/road-stress-tests/loader-*',route=>route.fulfill({json:jobs.find(job=>route.request().url().endsWith(job.id))}));
  await page.route('**/api/v1/road-stress-tests/loader-*/geometry',route=>route.fulfill({json:{lines:[[[37.6,55.75],[34.5,57.5],[30.3,59.9]]]}}));
  await page.addInitScript(jobs=>{
    const session={version:1,id:'loader-check',createdAt:Date.now(),updatedAt:Date.now(),draft:'',status:'done',error:null,messages:[{id:'answer',role:'assistant',content:'Сравниваю два варианта перекрытия дороги.',complete:true,steps:[],charts:[],tables:[],mapCommands:[],stressTests:jobs}]};
    localStorage.setItem('plexus.chat.session.v1.loader-check',JSON.stringify(session));
    localStorage.setItem('plexus.chat.active.v1','loader-check');
  },jobs);
  await page.goto('http://127.0.0.1:5187/?region=18000000&season=road&panel=chat');
  await page.getByText('64% этапа',{exact:true}).waitFor();
  await page.getByRole('button',{name:'Показать участок на карте'}).first().click();
  const map=page.locator('[data-stress-job="loader-one"]');
  await map.waitFor();
  await page.waitForFunction(()=>document.querySelector('[data-stress-job="loader-one"]')?.dataset.stressClosed==='1');
  if(await map.getAttribute('data-stress-points')!=='0')throw Error('Unexpected settlement points');
  await page.waitForTimeout(500);
  await page.screenshot({path:'work/chat-loader/desktop.png'});
  console.log(JSON.stringify({errors,closed:await map.getAttribute('data-stress-closed'),points:await map.getAttribute('data-stress-points')}));
  await browser.close();
  if(errors.length)process.exitCode=1;
})();
