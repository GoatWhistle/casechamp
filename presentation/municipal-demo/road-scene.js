const laneRoads = [
  ['M270 430 C350 430 390 390 460 360 S600 310 680 280', 'flow', 0],
  ['M680 280 C690 230 710 180 760 120', 'closed', 0],
  ['M680 280 C770 300 860 310 970 340 S1070 380 1140 410', 'flow', .6],
  ['M460 360 C460 260 480 210 550 170 S690 130 760 120', 'detour', .4],
  ['M970 340 C1010 250 920 180 760 120', 'detour', 1],
  ['M100 460 C170 450 210 430 270 430', 'quiet', 0],
  ['M760 120 C810 85 875 65 950 60', 'quiet', 0],
  ['M1140 410 L1260 460', 'quiet', 0],
];
const laneCritical = [[680,280,'Сужение'],[460,360,'Узел объезда'],[760,120,'Подъезд к городу']];
function LaneMap() {
  const phase = dj().beat;
  const active = phase !== '6';
  const critical = phase === '6.2';
  return (0,z.jsxs)('svg',{className:'municipal-map lane-map',viewBox:'0 0 1340 640',role:'img','aria-label':'Перекрытие полосы и перераспределение нагрузки',children:[
    (0,z.jsx)('rect',{width:1340,height:640,fill:'#edf3f0'}),
    (0,z.jsx)('path',{d:'M0 150 Q300 70 530 280 T1340 180 L1340 0 H0Z',fill:'#e0ebe3'}),
    (0,z.jsx)('path',{d:'M0 530 Q450 420 650 600 T1340 510 V640 H0Z',fill:'#e0ebe3'}),
    ...laneRoads.map(([d,kind],i)=>(0,z.jsx)('path',{d,className:'lane-road'},'base'+i)),
    ...laneRoads.map(([d,kind],i)=>(0,z.jsx)('path',{d,className:'lane-baseline'},'green'+i)),
    ...(active?laneRoads.filter(([,kind])=>kind!=='quiet').map(([d,kind,delay],i)=>(0,z.jsx)('path',{d,pathLength:1,className:'lane-impact '+kind,'data-part':'flow','data-delay':delay},'impact'+i)):[]),
    ...[[270,430,'Пятигорск'],[760,120,'Минеральные Воды'],[1140,410,'Георгиевск']].map(([x,y,label])=>(0,z.jsxs)('g',{children:[(0,z.jsx)('circle',{cx:x,cy:y,r:8,fill:'#2b4e43',stroke:'white',strokeWidth:3}),(0,z.jsx)('text',{x,y:y+40,textAnchor:'middle',className:'lane-city',children:label})]},label)),
    active?(0,z.jsxs)('g',{className:'lane-barrier','data-part':'barrier',children:[(0,z.jsx)('rect',{x:645,y:220,width:85,height:36,rx:8,fill:'#c53e34'}),(0,z.jsx)('text',{x:687,y:245,textAnchor:'middle',fill:'white',fontSize:20,fontWeight:650,children:'−1 полоса'})]}):null,
    ...(critical?laneCritical.map(([x,y,label],i)=>(0,z.jsxs)('g',{'data-part':'critical',className:'lane-critical',children:[(0,z.jsx)('circle',{cx:x,cy:y,r:24,fill:'#c53e341a'}),(0,z.jsx)('circle',{cx:x,cy:y,r:13,fill:'#c53e34',stroke:'white',strokeWidth:3}),(0,z.jsx)('text',{x,y:y+5,textAnchor:'middle',fill:'white',fontSize:14,fontWeight:700,children:String(i+1)}),(0,z.jsx)('text',{x:x+30,y:y-22,className:'lane-critical-label',children:label})]},label)):[]),
    (0,z.jsx)('text',{x:36,y:605,className:'municipal-map-label',children:active?'Красный: сужение / оранжевый: нагрузка на обходных связях':'Исходная дорожная сеть · схема'}),
  ]});
}
function LaneScene() {
  const phase=dj().beat;
  const base=municipalViews.find(v=>v.number===6);
  const views={
    '6':{heading:'Перекрываем одну полосу',eyebrow:'Дорожный сценарий',prompt:'Перекрой одну полосу и покажи, где появятся критические точки.',answer:'Сравню исходную сеть и сеть с перекрытой полосой. Результат покажу на дорогах.',metrics:[['1 полоса','Выбранное ограничение'],['Тот же спрос','До и после'],['Сеть края','Перерасчёт маршрутов']],caption:'Задаём ограничение на конкретном участке.'},
    '6.1':{heading:'Потоки перераспределяются',eyebrow:'Пересчёт после перекрытия',prompt:'Перекрой одну полосу и покажи, где появятся критические точки.',answer:'Ограничение задано. Цвет показывает, как нагрузка распространяется по соседним связям.',metrics:[['Сужение','Пропускная способность ниже'],['Объезд','Поток переходит на соседние связи'],['Пересчёт','Новая нагрузка на сети']],caption:'Цвет движется от перекрытия к затронутым связям.'},
    '6.2':{heading:'Критические точки после перекрытия',eyebrow:'Результат сценария',prompt:'Где теперь критические точки?',answer:'Выделены сужение, узел объезда и подъезд к городу. Их проверяем перед выбором мер.',metrics:[['01','Сужение'],['02','Узел объезда'],['03','Подъезд к городу']],caption:'Три точки внимания прямо на схеме дорог.'},
  };
  const view={...base,...views[phase],road:true,rows:[['Ограничение','Перекрыта одна полоса'],['Сравнение','Исходная и изменённая сеть'],['На карте','Затронутые дороги и критические узлы']],note:'Демонстрационный сценарий. Геометрия и распространение нагрузки показаны схематично.'};
  return (0,z.jsx)(MunicipalDemo,{view});
}
const laneScene={number:6,name:'Перекрытие полосы',Component:LaneScene,beats:[
  {id:'6',title:'Дорожный сценарий: *перекрываем одну полосу*',auto:true,hold:1.4,async run({run,part}){run.animate(part('evidence'),Sj,{dur:.5});await run.sleep(.6);}},
  {id:'6.1',title:'Пересчёт: *цвет распространяется по дорогам*',auto:true,hold:.8,async run({run,parts,part}){
    run.animate(part('barrier'),wj,{dur:.5});
    for(const path of parts('flow'))run.animate(path,[{strokeDasharray:'1',strokeDashoffset:1},{strokeDasharray:'1',strokeDashoffset:0}],{dur:3.5,delay:Number(path.dataset.delay),ease:'inOut'});
    await run.sleep(5);
  }},
  {id:'6.2',title:'После перекрытия: *где критические точки*',async run({run,parts}){run.all(parts('critical'),Cj,{dur:.5,stagger:.2});await run.sleep(1);}},
]};
$9=$9.map(scene=>scene.number===6?laneScene:scene);
