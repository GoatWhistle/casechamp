const municipalViews = [
  {
    number: 2, name: 'Муниципалитеты', title: 'Ставропольский край: *видим различия внутри региона*',
    region: 'Ставропольский край', selected: 'osm-relation-1030121',
    prompt: 'Покажи, где в крае хуже доступность МФЦ.',
    answer: 'Александровский округ: все 21 измеренная точка дальше часа от найденных МФЦ. Начнём с самых удалённых.',
    heading: 'Александровский округ', eyebrow: 'Приоритет для разбора',
    metrics: [['84,12', 'Связность с городами'], ['−15,04 п.', 'К уровню края'], ['21 из 21', 'Точек дальше 60 минут']],
    note: 'Дефицит относительно каталога МФЦ. Точки не равны доле жителей.',
    caption: 'Край → муниципалитет → конкретное место',
    rows: [['Территория', 'Александровский округ'], ['Показатель', 'МФЦ: до 60 минут'], ['Что проверяем', 'Где поездка занимает больше времени']],
  },
  {
    number: 3, name: 'Школы и медицина', title: 'Один муниципалитет: *разные виды доступности*',
    region: 'Пятигорск', selected: 'osm-relation-1030988', zoom: true,
    prompt: 'Покажи школы и медицину в Пятигорске.',
    answer: 'Доступность различается по цели поездки. Смотрите показатели отдельно: пешком до школы, на автомобиле до медицинского объекта.',
    heading: 'Городской округ Пятигорск', eyebrow: 'Школы / медицина',
    metrics: [['1 088 м', 'Средний путь пешком к школе'], ['7,4 мин', 'Средняя поездка к медобъекту'], ['11,3 мин', 'Средняя поездка к МФЦ']],
    rows: [['Школы', '8 308 жилых опорных точек'], ['Медицина / МФЦ', '8 опорных точек населённых пунктов'], ['Пояснения', 'Способ поездки и охват рядом с показателем']],
    note: 'Средние по измеренным точкам. Близость медобъекта не подтверждает профиль и возможность приёма.',
    caption: 'Показатели в карточке. Короткая интерпретация в чате.',
  },
  {
    number: 4, name: 'Точки дефицита', title: 'От среднего по округу *к конкретному селу*',
    region: 'Александровский округ', selected: 'osm-relation-1030121', zoom: true, points: true,
    prompt: 'Покажи самые удалённые точки этого округа.',
    answer: 'Грушевское: 131 минута до найденного МФЦ. Выделил точки и учреждение на карте. Здесь нужен разбор маршрута и полноты каталога.',
    heading: 'Село Грушевское', eyebrow: 'Самая удалённая точка в выборке',
    metrics: [['131 мин', 'До найденного МФЦ'], ['125 мин', 'P90 по округу'], ['60 мин', 'Порог сравнения']],
    rows: [['Откуда', 'Село Грушевское'], ['Куда', 'МФЦ, Ставрополь, ул. Голенева, 21'], ['На карте', 'Точки и найденное учреждение']],
    note: 'Пунктир показывает направление к учреждению, а не геометрию дороги. Каталог объектов неполный.',
    caption: 'Видно, где проблема и к какому учреждению считается доступ.',
  },
  {
    number: 5, name: 'Без автомобиля', title: 'Без автомобиля: *пешком, ожидание и автобус*',
    region: 'Пятигорск / Минеральные Воды', selected: 'osm-relation-1030988', transit: true, zoom: true,
    prompt: 'Как добраться из Пятигорска в Минеральные Воды без машины?',
    answer: 'При выходе в 14:00 прибытие в 15:14. Один автобус; в итог включены подходы пешком и ожидание.',
    heading: 'Пятигорск / Минеральные Воды', eyebrow: 'Маршрут без автомобиля',
    metrics: [['14:00', 'Выход'], ['15:14', 'Прибытие'], ['1 автобус', 'Без пересадки']],
    rows: [['Пешком до остановки', '4 мин 44 с'], ['Ожидание / автобус', '25 мин 16 с / 35 мин'], ['Пешком до назначения', '9 мин 39 с']],
    note: 'Сохранённое расписание. На карте остановки; геометрия автобусного пути не подтверждена.',
    caption: 'Время в пути включает ожидание, а не только движение.',
  },
  {
    number: 6, name: 'Изменение дороги', title: 'Проверяем вмешательство *на уровне муниципалитета*',
    region: 'Ставропольский край', selected: 'osm-relation-1030121',
    prompt: 'Что сравнить перед расширением или закрытием дороги?',
    answer: 'Местную связность, доступ к учреждениям и нагрузку. Эффект на округ рассматриваем отдельно от среднего по краю.',
    heading: 'Дорожный сценарий', eyebrow: 'Постановка сравнения',
    metrics: [['+1 полоса', 'Допустимое расширение'], ['Закрытие', 'Уязвимость связи'], ['До / после', 'Один исходный спрос']],
    rows: [['Связность', 'Муниципалитет и край отдельно'], ['Социальный доступ', 'Медицина, МФЦ и другие услуги'], ['Нагрузка', 'Потерянный спрос отдельно от экономии времени']],
    note: 'В этой демонстрации показана постановка сценария. Проверка итоговых эффектов ещё не завершена.',
    caption: 'Улучшение подтверждается результатом расчёта.',
  },
];

function municipalProjection(view) {
  const chosen = municipalData.features.find(f => f.id === view.selected);
  let points = (view.zoom ? [chosen] : municipalData.features).flatMap(f => f.rings.flat());
  if (view.points) points = [...points, ...municipalData.points.map(p => p.xy), municipalData.facility.xy];
  if (view.transit) points = municipalData.transit.points.map(p => [p.longitude, p.latitude]);
  let xs = points.map(p => p[0] * .72), ys = points.map(p => -p[1]);
  const lowX = Math.min(...xs), highX = Math.max(...xs), lowY = Math.min(...ys), highY = Math.max(...ys);
  const scale = Math.min(1120 / (highX-lowX), 470 / (highY-lowY));
  return ([x,y]) => [110 + (x*.72-lowX)*scale + (1120-(highX-lowX)*scale)/2, 90 + (-y-lowY)*scale + (470-(highY-lowY)*scale)/2];
}

function MunicipalMap({ view }) {
  const project = municipalProjection(view);
  const path = rings => rings.map(ring => ring.map((p,i) => `${i ? 'L' : 'M'}${project(p).map(n => n.toFixed(1)).join(',')}`).join(' ')+'Z').join(' ');
  const marker = (xy, name, key, kind='point') => {
    const [cx,cy] = project(xy);
    return (0,z.jsxs)('g', {className:'municipal-marker '+kind, children:[
      (0,z.jsx)('circle',{cx,cy,r:kind==='facility'?10:7}),
      name ? (0,z.jsx)('text',{x:cx+14,y:cy-13,children:name}) : null,
    ]},key);
  };
  const connection = (a,b,key) => {
    const [x1,y1]=project(a),[x2,y2]=project(b);
    return (0,z.jsx)('line',{x1,y1,x2,y2,className:'municipal-connection'},key);
  };
  return (0,z.jsxs)('svg',{viewBox:'0 0 1340 640',className:'municipal-map',role:'img','aria-label':view.region,children:[
    (0,z.jsx)('rect',{width:1340,height:640,fill:'#edf3f0'}),
    ...municipalData.features.map(f => (0,z.jsx)('path',{d:path(f.rings),className:'municipal-boundary','data-selected':f.id===view.selected},f.id)),
    view.points ? connection(municipalData.points[0].xy,municipalData.facility.xy,'mfc') : null,
    ...(view.points ? municipalData.points.map((p,i)=>marker(p.xy,i===0?'Грушевское':null,p.name)) : []),
    view.points ? marker(municipalData.facility.xy,'МФЦ · Ставрополь','facility','facility') : null,
    ...(view.transit ? municipalData.transit.points.filter(p=>p.role==='stop').map(p=>marker([p.longitude,p.latitude],p.id==='26015'?'Пятигорск':'Минеральные Воды',p.id,'facility')) : []),
    view.transit ? connection([43.0714,44.0309],[43.118,44.1988],'bus') : null,
    (0,z.jsx)('text',{x:36,y:610,className:'municipal-map-label',children:view.transit?'Остановки маршрута':view.points?'Точки доступа и учреждение':'Муниципальные границы Ставропольского края'}),
  ]});
}

function MunicipalDemo({ view }) {
  return (0,z.jsxs)('div',{className:'municipal-demo',children:[
    (0,z.jsxs)('main',{className:'municipal-workspace',children:[
      (0,z.jsxs)('div',{className:'municipal-toolbar',children:[(0,z.jsx)('strong',{children:view.region}),(0,z.jsx)('span',{children:'Муниципалитеты'})]}),
      view.road ? (0,z.jsx)(LaneMap,{}) : (0,z.jsx)(MunicipalMap,{view}),
      (0,z.jsxs)('section',{className:'municipal-evidence','data-part':'evidence',children:[
        (0,z.jsx)('p',{className:'municipal-eyebrow',children:view.eyebrow}),
        (0,z.jsx)('h2',{children:view.heading}),
        (0,z.jsx)('div',{className:'municipal-metrics',children:view.metrics.map(([value,label])=>(0,z.jsxs)('div',{children:[(0,z.jsx)('strong',{children:value}),(0,z.jsx)('span',{children:label})]},label))}),
        (0,z.jsx)('p',{className:'municipal-note',children:view.note}),
      ]}),
      (0,z.jsx)('p',{className:'municipal-caption',children:view.caption}),
    ]}),
    (0,z.jsxs)('aside',{className:'municipal-chat',children:[
      (0,z.jsx)('div',{className:'municipal-chat-title',children:'Plexus'}),
      (0,z.jsx)('div',{className:'municipal-question','data-part':'question',children:view.prompt}),
      (0,z.jsx)('div',{className:'municipal-answer','data-part':'answer',children:view.answer}),
      (0,z.jsx)('p',{className:'municipal-chat-hint',children:'Результат на карте и в карточке'}),
      (0,z.jsx)('div',{className:'municipal-composer',children:'Спросить о выбранной территории'}),
    ]}),
    (0,z.jsxs)('section',{className:'municipal-detail','data-part':'detail',children:[
      (0,z.jsx)('h3',{children:'Подробности'}),
      ...view.rows.map(([label,value])=>(0,z.jsxs)('div',{className:'municipal-detail-row',children:[(0,z.jsx)('span',{children:label}),(0,z.jsx)('strong',{children:value})]},label)),
    ]}),
  ]});
}

const municipalScenes = municipalViews.map(view => ({
  number:view.number,name:view.name,Component:()=> (0,z.jsx)(MunicipalDemo,{view}),
  beats:[{id:String(view.number),title:view.title,async run({run,part}) {
    run.animate(part('question'),Cj,{dur:.25});
    run.animate(part('evidence'),Sj,{dur:.45});
    run.animate(part('detail'),Cj,{dur:.35});
    run.animate(part('answer'),Cj,{dur:.25});
    await run.sleep(.45);
  }}],
}));

J_e.beats[0].run = async ({run,root,parts}) => {
  $7(run,root,{start:0,period:1});
  run.all(parts('promise'),G_e,{dur:.5,stagger:.1});
  run.all(parts('foot'),Cj,{dur:.4});
  await run.sleep(.6);
};
sye = ['Муниципальные индексы', 'Школы, медицина и МФЦ', 'Точки дефицита на карте', 'Поездки без автомобиля'];
cye = [
  {title:'Проверить дорожные вмешательства',text:'расширение и закрытие, местный эффект и нагрузка'},
  {title:'Уточнить учреждения и расписания',text:'профиль, координаты, фактическая работа'},
  {title:'Пилот в Ставропольском крае',text:'сверка приоритетов с муниципалитетами'},
  {title:'Расширять проверенное покрытие',text:'тот же путь анализа для других территорий'},
];
dye = [
  {who:'Региональный аналитик',ask:'Каким округам уделить внимание?',how:'сравнение муниципалитетов'},
  {who:'Муниципалитет',ask:'Где конкретно сложно добраться?',how:'точки, учреждения и время поездки'},
  {who:'Житель',ask:'Что доступно рядом с домом?',how:'школа, медицина, путь без автомобиля'},
];
Z9 = [
  {title:'Ставропольский край',text:'единый пример от региона до конкретного места'},
  {title:'Проверка на месте',text:'сверка объектов, маршрутов и местных приоритетов'},
  {title:'Другие территории',text:'перенос после проверки данных и расчётов'},
];
$9 = [J_e,...municipalScenes,uye,{number:8,name:'Польза',Component:fye,beats:[
  {id:'8',title:'Одна карта: *три задачи пользователя*',run:pye},
  {id:'8.1',title:'Начинаем со *Ставропольского края*',run:mye},
]},Cve];
