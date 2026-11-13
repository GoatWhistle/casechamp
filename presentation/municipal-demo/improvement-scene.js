const improvementImages=Object.values(improvementFrames).map(src=>{const image=new Image();image.src=src;image.decode().catch(()=>{});return image});
const improvementFormat=value=>value.toFixed(2).replace('.',',');
function ImprovementScene(){
 return z.jsxs('div',{className:'improvement-film',children:[
  z.jsxs('div',{className:'improvement-camera','data-part':'im-camera',children:[z.jsx('img',{src:improvementFrames.neutral,alt:'Кочубеевский округ'}),z.jsx('img',{'data-part':'im-before',style:{opacity:0},src:improvementFrames.before,alt:'Кочубеевский округ, критический участок трассы «Кавказ»'}),z.jsx('img',{src:improvementFrames.after,alt:'Сценарий расширения участка','data-part':'im-after',style:{opacity:0}})]}),
  z.jsxs('div',{className:'improvement-heading','data-part':'im-heading',children:[z.jsx('small',{children:'Кочубеевский муниципальный округ'}),z.jsx('h2',{children:'Узкое место на трассе «Кавказ»'}),z.jsx('p',{children:'Поток превышает пропускную способность участка.'})]}),
  z.jsx('span',{className:'improvement-pulse','data-part':'im-pin',style:{left:improvementMeta.center[0]*100+'%',top:improvementMeta.center[1]*100+'%'}}),
  z.jsxs('article',{className:'improvement-proposal','data-part':'im-proposal',children:[z.jsx('small',{children:'Трасса «Кавказ» · предлагаем'}),z.jsx('h3',{children:'+1 полоса в каждом направлении'}),z.jsx('div',{className:'improvement-lanes',children:[0,1].map((v)=>z.jsx('span',{'data-part':v===1?'im-new-lane':'im-lane',className:v===1?'is-new':'',children:v===1?'Новая полоса':'→'},v))}),z.jsx('p',{children:'Одна полоса → две в каждом направлении.'})]}),
  z.jsxs('article',{className:'improvement-result','data-part':'im-result',children:[z.jsx('small',{children:'Доступность округа · индекс сценария'}),z.jsxs('div',{className:'improvement-counter',children:[z.jsx('span',{children:'100,00'}),z.jsx('span',{children:'→'}),z.jsx('strong',{'data-part':'im-index',children:improvementFormat(improvementData.after)}),z.jsx('b',{'data-part':'im-delta',children:'+'+improvementFormat(improvementData.after-100)+' п.'})]}),z.jsx('p',{children:'Поездки к рынкам становятся быстрее.'}),z.jsxs('div',{className:'improvement-comparison',children:[z.jsx('div',{className:'improvement-row-label',children:'Загрузка участка'}),z.jsxs('div',{children:[z.jsx('small',{children:'ДО'}),z.jsx('strong',{className:'load-before',children:'142%'}),z.jsx('span',{children:'Перегрузка на 42%'})]}),z.jsxs('div',{children:[z.jsx('small',{children:'ПОСЛЕ'}),z.jsx('strong',{children:'71%'}),z.jsx('span',{children:'Запас мощности 29%'})]})]}),z.jsx('div',{className:'improvement-load-track',children:z.jsx('i',{'data-part':'im-load'})}),z.jsxs('div',{className:'improvement-time',children:[z.jsx('span',{children:'Проезд участка'}),z.jsx('strong',{children:improvementData.flows[0].minutes.toFixed(1).replace('.',',')+' → '+improvementData.flows[1].minutes.toFixed(1).replace('.',',')+' мин'}),z.jsx('b',{children:'−'+(improvementData.flows[0].minutes-improvementData.flows[1].minutes).toFixed(1).replace('.',',')+' мин'})]}),z.jsx('small',{children:'До = 100 · одинаковый спрос и база сравнения'})]})
 ]});
}
function improvementZoom(){const width=1920-352*pj,height=976,scale=2.2;return `translate(${width*.39-improvementMeta.center[0]*width*scale}px,${height*.46-improvementMeta.center[1]*height*scale}px) scale(${scale})`}
async function improvementReady(c){await Promise.all([...c.root.querySelectorAll('.improvement-camera img')].map(i=>i.decode()))}
const improvementScene={number:11,name:'Улучшение муниципалитета',product:true,session:'region',Component:ImprovementScene,beats:[{
 id:'5.2',title:'Кочубеевский округ: *найти критический участок*',auto:true,hold:1.4,
 async run(c){
  await demoStartScene(c);await improvementReady(c);
  await demoAsk(c,'Найди критические участки Кочубеевского округа.','Выделен перегруженный участок трассы «Кавказ». В модели спрос достигает 142% пропускной способности. Проверим расширение.',async()=>{
   c.run.animate(c.part('im-before'),[{opacity:0},{opacity:1}],{dur:.8});
   c.run.animate(c.part('im-heading'),Sj,{dur:1});
   c.run.animate(c.part('im-pin'),[{opacity:0,boxShadow:'0 0 0 0 #e7473260'},{opacity:1,boxShadow:'0 0 0 35px #e7473200'}],{dur:1.7});
   await c.run.sleep(1.2);
   c.run.animate(c.part('im-pin'),[{opacity:1},{opacity:0}],{dur:.3});
   c.run.animate(c.part('im-camera'),[{transform:'none'},{transform:improvementZoom()}],{dur:1.8,ease:'inOut'});
   await c.run.sleep(2);
  });
 }
},{id:'5.3',title:'Предлагаем расширение: *как меняется индекс*',async run(c){
 await demoAsk(c,'Предложи исправление и покажи изменение индекса округа.','Добавляем по полосе в каждом направлении. Индекс сценария: 100 → 101,73. Нагрузка выбранного участка: 142% → 71%. Дальше — проверить стоимость и возможность расширения.',async()=>{
  c.run.animate(c.part('im-heading'),[{opacity:1},{opacity:0}],{dur:.4});
  c.run.animate(c.part('im-pin'),[{opacity:1},{opacity:0}],{dur:.4});
  c.run.animate(c.part('im-proposal'),Sj,{dur:.9});
  c.run.animate(c.part('im-new-lane'),[{opacity:0,transform:'scaleX(0)'},{opacity:1,transform:'scaleX(1)'}],{dur:1.4,delay:.6});
  await c.run.sleep(2.2);
  c.run.animate(c.part('im-after'),[{opacity:0,clipPath:`circle(0% at ${improvementMeta.center[0]*100}% ${improvementMeta.center[1]*100}%)`},{opacity:1,clipPath:`circle(120% at ${improvementMeta.center[0]*100}% ${improvementMeta.center[1]*100}%)`}],{dur:1.8});
  await c.run.sleep(1.9);
  c.run.animate(c.part('im-camera'),[{transform:improvementZoom()},{transform:'none'}],{dur:1.8,ease:'inOut'});
  await c.run.sleep(1.9);
  c.run.animate(c.part('im-result'),Sj,{dur:1.1});
  c.run.animate(c.part('im-load'),[{transform:'scaleX(.945)',background:'#e74732'},{transform:'scaleX(.474)',background:'#00a875'}],{dur:2});
  await c.run.tween(2.5,t=>{c.part('im-index').textContent=improvementFormat(100+(improvementData.after-100)*t);c.part('im-delta').textContent='+'+improvementFormat((improvementData.after-100)*t)+' п.'},'out',.3);
 });
}}]};
$9.splice($9.indexOf(z_e)+1,0,improvementScene);
$9.forEach((scene,index)=>{scene.number=index+1});
