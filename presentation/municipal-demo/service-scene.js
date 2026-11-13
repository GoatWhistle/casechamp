const serviceImages=Object.values(serviceFrames).map(src=>{const image=new Image();image.src=src;image.decode().catch(()=>{});return image});
const serviceCopy=[
 {prompt:'Покажи доступность медицины в Александровском округе.',reply:'19 из 21 населённого пункта — в пределах часа на машине до известного медобъекта. Два пункта — дальше. Специализация учреждений не подтверждена.',detail:'19 населённых пунктов — в пределах часа. Из двух ехать дольше.',note:'До известного медобъекта · профиль помощи не подтверждён'},
 {prompt:'А насколько доступны школы пешком?',reply:'Школа в пределах 500 метров пешком для 9,1% проверенных жилых точек. Для 348 точек путь длиннее. Это доля точек, не детей.',detail:'У 348 жилых точек школа дальше 500 метров пешком.',note:'383 жилые опорные точки · не доля детей и не оценка качества школы'},
 {prompt:'Покажи доступность остановок.',reply:'Остановка в пределах 500 метров пешком для 43,3% проверенных жилых точек. Для 217 точек идти дальше. Наличие остановки не гарантирует регулярный рейс.',detail:'У 217 жилых точек остановка дальше 500 метров пешком.',note:'383 жилые опорные точки · частота рейсов не учитывается'}
];
function ServiceScene(){return z.jsxs('div',{className:'service-film',children:[
 z.jsxs('div',{className:'service-camera','data-part':'service-camera',children:[z.jsx('img',{className:'service-map',src:serviceFrames.neutral,alt:'Александровский муниципальный округ'}),
 ...serviceData.services.map(s=>z.jsx('img',{className:'service-map','data-part':'service-map-'+s.id,src:serviceFrames[s.id],style:{opacity:0},alt:s.title},s.id))]}),
 z.jsx('div',{className:'service-cards',children:serviceData.services.map((s,i)=>z.jsxs('article',{'data-part':'service-card-'+i,children:[z.jsx('header',{children:s.title}),z.jsx('p',{className:'service-threshold',children:s.thresholdLabel}),z.jsxs('div',{className:'service-number',children:[z.jsx('strong',{'data-part':'service-value-'+i,children:'—'}),z.jsx('span',{children:'%'})]}),z.jsx('div',{className:'service-bar',children:z.jsx('i',{'data-part':'service-bar-'+i})}),z.jsx('small',{'data-part':'service-count-'+i,children:i===0?'Доля населённых пунктов':'Доля жилых опорных точек'})]},s.id))}),
 z.jsxs('div',{className:'service-explanation','data-part':'service-explanation',children:[z.jsx('strong',{'data-part':'service-detail',children:''}),z.jsx('p',{'data-part':'service-note',children:''}),z.jsxs('div',{className:'service-legend',children:[z.jsx('span',{children:'● В пределах порога',className:'within'}),z.jsx('span',{children:'● Дальше порога',className:'outside'}),z.jsx('span',{children:'По известным объектам и сохранённым маршрутам'})]})]})
]})}
function serviceZoom(){const width=1920-352*pj,height=976,scale=2.5;return `translate(${width*.5-serviceMeta.focus[0]*width*scale}px,${height*.58-serviceMeta.focus[1]*height*scale}px) scale(${scale})`}
const serviceScene={number:12,name:'Медицина, школы, остановки',product:true,session:'region',Component:ServiceScene,beats:[{id:'4.1',title:'Александровский округ: *доступность трёх услуг*',async run(c){
 await demoStartScene(c);
 await Promise.all([...c.root.querySelectorAll('.service-map')].map(image=>image.decode()));
 await demoAsk(c,'Покажи доступность медицины, школ и остановок в Александровском округе.','Медицина — 90,5% населённых пунктов в пределах часа на машине. Школы — 9,1%, остановки — 43,3% жилых точек в пределах 500 м пешком. Основной дефицит — пешая доступность школ. Точки и пороги показаны на карте.',async()=>{
  c.run.all([0,1,2].map(n=>c.part('service-card-'+n)),Sj,{dur:.65,stagger:.1});
  for(let i=0;i<serviceData.services.length;i++){
   const s=serviceData.services[i];
   for(let n=0;n<3;n++)c.part('service-card-'+n).classList.toggle('is-active',n===i);
   if(i>0)c.run.animate(c.part('service-map-'+serviceData.services[i-1].id),[{opacity:1},{opacity:0}],{dur:.7});
   if(i===1){c.run.animate(c.part('service-camera'),[{transform:'none'},{transform:serviceZoom()}],{dur:1.8,ease:'inOut'});await c.run.sleep(1.8)}
   c.run.animate(c.part('service-map-'+s.id),[{opacity:0,clipPath:'circle(0% at 50% 50%)'},{opacity:1,clipPath:'circle(100% at 50% 50%)'}],{dur:1.7,ease:'inOut'});
   c.part('service-detail').textContent=serviceCopy[i].detail;
   c.part('service-note').textContent=serviceCopy[i].note;
   c.run.animate(c.part('service-explanation'),[{opacity:0,transform:'translateY(12px)'},{opacity:1,transform:'none'}],{dur:.8,delay:.8});
   await c.run.tween(2.1,t=>{c.part('service-value-'+i).textContent=(s.value*t).toFixed(1).replace('.',',');c.part('service-bar-'+i).style.transform=`scaleX(${s.value*t/100})`},'out');
   c.part('service-count-'+i).textContent=s.within+' из '+s.total+(i===0?' населённых пунктов':' жилых точек')+' в пределах порога';
   await c.run.sleep(1);
  }
 });
}}]};
$9.splice($9.indexOf(Ave)+1,0,serviceScene);
$9.forEach((scene,index)=>{scene.number=index+1});
if(['#4.2','#4.3'].includes(location.hash))history.replaceState(null,'',location.search+'#4.1');
