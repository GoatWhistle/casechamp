let demoReply = '';
yde = async function(request, signal, emit) {
  if(signal?.aborted) return;
  const text=demoReply;
  const chunks=Mj.run?.fast?[text]:(text.match(/\S+\s*/g)||[]);
  for(let i=0;i<chunks.length;i++){
    if(signal?.aborted) return;
    emit({type:'delta',text:chunks[i],code:''});
    if(i<chunks.length-1&&!Mj.run?.fast) await new Promise(resolve=>setTimeout(resolve,110));
  }
  emit({type:'done',text:'',code:''});
};
hj.settle = async function(run) {
  await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
  await run.until(()=>!this.answering(),10);
};
const featureCollection = features => ({type:'FeatureCollection',features});
const demoMunicipalities = featureCollection(municipalData.features.map(f=>({type:'Feature',properties:{id:f.id,name:f.name},geometry:{type:'Polygon',coordinates:f.rings}})));
function demoLayer(map,id,data,type,paint,layout={}) {
  if(map.getSource(id)) map.getSource(id).setData(data);
  else {map.addSource(id,{type:'geojson',data});map.addLayer({id,type,source:id,paint,layout});}
}
function demoSelection(map,features) {
  const data=featureCollection(features);
  demoLayer(map,'demo-selection-halo',data,'line',{'line-color':'#ffffff','line-width':7,'line-opacity':.95});
  demoLayer(map,'demo-selection-outline',data,'line',{'line-color':'#0768dc','line-width':3,'line-opacity':1});
  map.moveLayer('demo-selection-halo');
  map.moveLayer('demo-selection-outline');
}
async function demoMap(context,kind) {
  await context.run.until(()=>globalThis.__plexusDemoMap?.isStyleLoaded(),20);
  const map=globalThis.__plexusDemoMap;
  if(!map?.isStyleLoaded()) throw new Error('Original map is not ready');
  demoLayer(map,'demo-municipalities',demoMunicipalities,'fill',{'fill-color':'#557a78','fill-opacity':.14});
  demoLayer(map,'demo-boundaries',demoMunicipalities,'line',{'line-color':'#607b78','line-width':1.2,'line-opacity':.65});
  map.setPaintProperty('demo-municipalities','fill-color','#557a78');
  if(map.getLayer('demo-social'))map.setLayoutProperty('demo-social','visibility','none');
  demoSelection(map,[demoRegion]);
  const road=kind==='road';
  const regionPoints=demoRegion.geometry.coordinates.flat(2);
  const regionBounds=[[Math.min(...regionPoints.map(p=>p[0])),Math.min(...regionPoints.map(p=>p[1]))],[Math.max(...regionPoints.map(p=>p[0])),Math.max(...regionPoints.map(p=>p[1]))]];
  map.stop();
  map.fitBounds(road?[[41.85,44.82],[42.3,45.16]]:regionBounds,{duration:context.run.fast?0:1100,padding:{top:60,bottom:70,left:65,right:65}});
  await context.run.until(()=>!map.isMoving(),5);
  if(road) demoLayer(map,'demo-roads',municipalRoads,'line',{'line-color':'#788d88','line-width':3,'line-opacity':.7});
}
async function demoFocusMunicipality(context,municipalityId='osm-relation-1030121') {
  const map=globalThis.__plexusDemoMap;
  const municipality=municipalData.features.find(f=>f.id===municipalityId);
  map.setPaintProperty('demo-municipalities','fill-color',['case',['==',['get','id'],municipality.id],'#e14b35','#557a78']);
  demoSelection(map,[demoMunicipalities.features.find(f=>f.properties.id===municipality.id)]);
  const points=municipality.rings.flat();
  const west=Math.min(...points.map(p=>p[0]));
  const east=Math.max(...points.map(p=>p[0]));
  const south=Math.min(...points.map(p=>p[1]));
  const north=Math.max(...points.map(p=>p[1]));
  map.fitBounds([[west,south],[east,north]],{duration:context.run.fast?0:1100,padding:{top:55,bottom:260,left:65,right:65}});
  await context.run.until(()=>!map.isMoving(),5);
}
async function demoStartScene(c){
  await hj.ready(c.run);
  hj.newChat()?.click();
  await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
}
async function demoAsk(context,prompt,reply,visual) {
  demoReply=reply;
  context.cursor.show(context.run,true);
  const field=hj.field();
  await Y7(context.driver,field,prompt,30);
  X7(field);
  await Promise.all([hj.settle(context.run),visual?.()]);
  context.cursor.show(context.run,false);
}
function DemoCard({name,value,rank,note}) {
  return z.jsx('div',{className:'region',children:z.jsxs('article',{className:'region-card municipal-reference-card','data-part':'card',children:[
    z.jsx('p',{className:'region-name',children:name}),
    z.jsx('strong',{className:'region-value','data-part':'metric-value',children:value}),
    z.jsx('p',{className:'region-rank','data-part':'metric-rank',children:rank}),
    z.jsx('p',{className:'region-note',children:note})]})});
}
async function demoReveal(context) {
  context.run.animate(context.part('card'),[{opacity:0,transform:'translateY(40px) scale(0.96)',filter:'blur(2px)'},{opacity:1,transform:'none',filter:'blur(0)'}],{dur:1.1});
  await context.run.sleep(1.1);
}
async function demoRevealMunicipality(c) {
  const value=c.part('metric-value');
  const rank=c.part('metric-rank');
  const format=number=>number.toFixed(2).replace('.',',');
  value.textContent='0,00';
  rank.textContent='−0,00 пункта к индексу края';
  c.run.animate(c.part('card'),[{opacity:0,transform:'translateY(28px) scale(.98)'},{opacity:1,transform:'none'}],{dur:1.8});
  await Promise.all([
    c.run.tween(2.4,progress=>{value.textContent=format(84.12*progress)},'out',.35),
    c.run.tween(2.2,progress=>{rank.textContent='−'+format(15.04*progress)+' пункта к индексу края'},'out',.65)
  ]);
}
oye.Component=()=>z.jsx(DemoCard,{name:'Александровский муниципальный округ',value:'84,12',rank:'−15,04 пункта к индексу края',note:'Связанность с рынками • сохранённый расчёт'});
oye.beats=[{
  id:'2',title:'Ставропольский край: *33 муниципалитета*',auto:true,hold:1.4,
  async run(c){
    await demoStartScene(c);
    await demoAsk(c,'Покажи Ставропольский край и его муниципалитеты.','Ставропольский край: 33 муниципалитета. Теперь сравним их связанность.',()=>demoMap(c,'municipal'));
  }
},{
  id:'2.1',title:'Выбираем муниципалитет: *где доступность ниже*',
  async run(c){
    await demoAsk(c,'Покажи проблемный округ и объясни почему.','Александровский округ: индекс 84,12 — на 15,04 пункта ниже края.',async()=>{
      await demoFocusMunicipality(c);
      lj({title:'Александровский округ: *где доступность ниже*'});
    });
    await demoRevealMunicipality(c);
  }
}];
Ave.session='region';
Ave.Component=()=>z.jsx(DemoCard,{name:'Новоселицкий округ · МФЦ',value:'Больше 2 часов',rank:'из пяти населённых пунктов до МФЦ',note:'На автомобиле · ближайший МФЦ в нашем каталоге. Из Щелкана — около 2 ч 30 мин.'});
Ave.beats=[{id:'4',title:'Новоселицкий округ: *до МФЦ больше двух часов*',async run(c){
  await demoStartScene(c);
  await demoAsk(c,'Покажи, откуда в Новоселицком округе до МФЦ больше двух часов.','Из Артезианского, Журавского, Китаевского, Падинского и Щелкана до ближайшего МФЦ в нашем каталоге — больше двух часов на машине. Из Щелкана — около 2 ч 30 мин.',async()=>{
    await demoMap(c,'municipal');
    await demoFocusMunicipality(c,socialExample.id);
    const map=globalThis.__plexusDemoMap;
    demoLayer(map,'demo-social',featureCollection(socialExample.points.map(p=>({type:'Feature',properties:{name:p.name,remote:p.minutes>120},geometry:{type:'Point',coordinates:p.xy}}))),'circle',{'circle-radius':6,'circle-color':['case',['get','remote'],'#e04434','#078d83'],'circle-stroke-color':'#fff','circle-stroke-width':2});
    map.setPaintProperty('demo-social','circle-color',['case',['get','remote'],'#e04434','#078d83']);
    map.setLayoutProperty('demo-social','visibility','visible');
  });
  await demoReveal(c);
}}];
sye=['Связанность региона и муниципалитетов','Школы, медицина и МФЦ','Закрытие и расширение участков','Агент и результаты на карте'];
cye=[{title:'Наблюдаемый поток',text:'сверить модель со счётчиками и временем поездок'},{title:'Пилот в Ставропольском крае',text:'реальные ремонты, ограничения и объезды'},{title:'Приоритет проектов',text:'эффект на связанность, услуги и стоимость'},{title:'Мониторинг',text:'обновление данных и сравнение сценариев'}];
dye=[{who:'Руководитель региона',ask:'Где связность хуже и почему?',how:'край → муниципалитет → населённый пункт'},{who:'Дорожное ведомство',ask:'Как изменится доступ при ремонте?',how:'полоса → время проезда → доступность'},{who:'Муниципалитет',ask:'Кто дальше всего от услуг?',how:'конкретные точки, пороги и покрытие данных'}];
Z9[0].text='Ставропольский край: ограничения полос, доступность услуг, сверка с наблюдениями';
const formulaRows=[['Связанность с рынками','Aᵢ = Σⱼ Pⱼ · 2^(−tᵢⱼ / 2)','t — часы; P — население рынка; полураспад — 2 часа'],['Индекс муниципалитета','Iₘ = 100 · (Σᵢ pᵢAᵢ / Σᵢ pᵢ) / B','p — население точки; B — фиксированная база сравнения'],['Доступность услуг','Sₖ(τ) = 100 · Σᵢ wᵢ · 1[dᵢₖ ≤ τ] / Σᵢ wᵢ','доля точек или жителей в пределах порога; веса указываются'],['Нагрузка и время','C = 1 800 · n;  t = t₀ · [1 + 0,15(q/C)⁴]','n — полосы направления; q — поток; ёмкость — допущение']];
const demoFormula={number:10,name:'Формулы',Component:()=>z.jsx('div',{className:'demo-formulas',children:formulaRows.map(([title,formula,note])=>z.jsxs('article',{'data-part':'formula',children:[z.jsx('p',{children:title}),z.jsx('strong',{children:formula}),z.jsx('small',{children:note})]},title))}),beats:[{id:'3.2',title:'Что считаем: *индексы и формулы*',async run(c){c.run.all(c.parts('formula'),Sj,{dur:.7,stagger:.15});await c.run.sleep(1.2);}}]};
$9=[J_e,oye,iye,demoFormula,Ave,z_e,F_e,uye,$9[7],Cve];
k_e=[{lead:'Связанность и доступность услуг разделены',detail:'общий индекс не заменяет проверку конкретных точек'},{lead:'База индекса зафиксирована',detail:'до и после сравниваются при одинаковой нормировке'},{lead:'Поток и число полос заданы явно',detail:'наблюдения отделены от модельных допущений'},{lead:'Результат можно воспроизвести',detail:'исходные данные и параметры сценария сохраняются'}];
$9.forEach((scene,index)=>{scene.number=index+1});

if(location.hash==='#3.0') history.replaceState(null,'',location.search+'#3');
F_e.beats=F_e.beats.filter(beat=>beat.id!=='6.1');
if(location.hash==='#6.1')history.replaceState(null,'',location.search+'#6');
