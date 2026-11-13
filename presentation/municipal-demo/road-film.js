const criticalExplanations=[
 {x:.410,y:.601,title:'Въезд на участок',meaning:'Здесь может накапливаться очередь.',action:'При росте очереди — дозировать въезд.'},
 {x:.389,y:.542,title:'Место сужения',meaning:'Здесь проверяем потерю скорости.',action:'Сравнить объезд и другое время работ.'},
 {x:.417,y:.515,title:'Выезд с участка',meaning:'Проверяем, не ушла ли перегрузка дальше.',action:'Проверить соседний узел и его режим.'}
];
const roadFrameCache=Object.values(roadFrames).map(src=>{const image=new Image();image.src=src;image.decode().catch(()=>{});return image});
function RoadFilm(){
  return z.jsxs('div',{className:'road-film',children:[
    z.jsx('div',{className:'road-film-camera','data-part':'camera',children:['before','closed','effect','critical'].map((state,index)=>z.jsx('img',{src:roadFrames[state],className:'road-film-frame','data-part':state,style:{opacity:index===0?1:0},alt:'',draggable:false},state))}),
    z.jsx('div',{className:'road-film-caption','data-part':'before-label',children:'Две полосы · одно направление'}),
    z.jsx('div',{className:'road-film-caption','data-part':'closed-label',children:'Одна полоса закрыта'}),
    z.jsx('div',{className:'road-film-caption','data-part':'effect-label',children:'Изменения на соседних участках'}),
    z.jsx('div',{className:'road-film-caption','data-part':'critical-label',children:'Критические точки'}),
    z.jsx('span',{className:'road-film-block','data-part':'block',children:'×'}),
    z.jsxs('div',{className:'road-film-metric','data-part':'capacity',children:[z.jsx('span',{children:'Пропускная способность'}),z.jsxs('div',{children:[z.jsx('strong',{children:'3 600'}),z.jsx('span',{children:'→'}),z.jsx('strong',{className:'road-film-red',children:'1 800'}),z.jsx('small',{children:'авт./ч'})]})]}),
    z.jsx('div',{className:'critical-pins',children:criticalExplanations.map((point,index)=>z.jsx('span',{className:'critical-pin','data-part':'critical-pin',style:{left:point.x*100+'%',top:point.y*100+'%'},children:index+1},index))}),
    z.jsx('div',{className:'critical-explanations',children:criticalExplanations.map((point,index)=>z.jsxs('article',{'data-part':'critical-explanation',children:[z.jsxs('header',{children:[z.jsx('b',{children:index+1}),z.jsx('strong',{children:point.title})]}),z.jsx('p',{children:point.meaning}),z.jsx('div',{'data-part':'critical-action',children:point.action})]},index))}),
    z.jsx('div',{className:'road-film-note',children:'Демо · точки проверки, не подтверждённые пробки'})
  ]});
}
async function filmCaption(c,part,show=true){
  c.run.animate(c.part(part),show?[{opacity:0,transform:'translateY(10px)'},{opacity:1,transform:'none'}]:[{opacity:1},{opacity:0}],{dur:.55});
  await c.run.sleep(.55);
}
function filmZoom(){
  const width=1920-352*pj;
  const height=976;
  const scale=3;
  return `translate(${width*.5-roadFrameMeta.center[0]*width*scale}px,${height*.43-roadFrameMeta.center[1]*height*scale}px) scale(${scale})`;
}
async function filmReady(c){
  await Promise.all([...c.root.querySelectorAll('.road-film-frame')].map(image=>image.decode()));
}
z_e.session='region';z_e.name='Одна полоса';z_e.Component=RoadFilm;
z_e.beats=[{id:'5',title:'Приближаем участок: *закрываем одну полосу*',auto:true,hold:.8,async run(c){
  await demoStartScene(c);await filmReady(c);
  await demoAsk(c,'Закрой одну полосу на выбранном участке.','Одна из двух полос закрыта. Пропускная способность уменьшилась вдвое.',async()=>{
    await filmCaption(c,'before-label');
    c.run.animate(c.part('camera'),[{transform:'none'},{transform:filmZoom()}],{dur:1.7,ease:'inOut'});
    await c.run.sleep(1.7);
    await filmCaption(c,'before-label',false);
    c.run.animate(c.part('closed'),[{opacity:0},{opacity:1}],{dur:.8});
    c.run.animate(c.part('block'),[{opacity:0,transform:'translate(-50%,-50%) scale(.6)'},{opacity:1,transform:'translate(-50%,-50%) scale(1)'}],{dur:.65});
    await filmCaption(c,'closed-label');
    await c.run.sleep(.8);
    c.run.animate(c.part('capacity'),Sj,{dur:.8});
    await c.run.sleep(1.1);
  });
}},{id:'5.1',title:'Отдаляем карту: *что изменилось вокруг*',async run(c){
  await demoAsk(c,'Покажи изменения вокруг и критические точки.','Точки показывают, где проверить очередь, скорость и перенос перегрузки. Действия — рядом с картой.',async()=>{
    await filmCaption(c,'closed-label',false);
    c.run.animate(c.part('capacity'),[{opacity:1},{opacity:0}],{dur:.4});
    c.run.animate(c.part('block'),[{opacity:1},{opacity:0}],{dur:.35});
    c.run.animate(c.part('camera'),[{transform:filmZoom()},{transform:'none'}],{dur:1.7,ease:'inOut'});
    await c.run.sleep(1.7);
    await filmCaption(c,'effect-label');
    c.run.animate(c.part('effect'),[{opacity:0,clipPath:`circle(0% at ${roadFrameMeta.center[0]*100}% ${roadFrameMeta.center[1]*100}%)`},{opacity:1,clipPath:`circle(120% at ${roadFrameMeta.center[0]*100}% ${roadFrameMeta.center[1]*100}%)`}],{dur:2.2,ease:'inOut'});
    await c.run.sleep(2.3);
    await filmCaption(c,'effect-label',false);
    c.run.animate(c.part('critical'),[{opacity:0},{opacity:1}],{dur:.8});
    await filmCaption(c,'critical-label');
    const pins=c.parts('critical-pin'),cards=c.parts('critical-explanation'),actions=c.parts('critical-action');
    for(let i=0;i<cards.length;i++){
      c.run.animate(pins[i],[{opacity:0,transform:'translate(-50%,-50%) scale(.6)'},{opacity:1,transform:'translate(-50%,-50%) scale(1)'}],{dur:.55});
      c.run.animate(cards[i],Sj,{dur:.65});
      c.run.animate(pins[i],[{boxShadow:'0 0 0 0 #e4483340'},{boxShadow:'0 0 0 22px #e4483300'}],{dur:1.1});
      await c.run.sleep(.8);
      c.run.animate(actions[i],Sj,{dur:.6});
      await c.run.sleep(1.1);
    }
  });
}}];
