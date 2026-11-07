'use client';

import {useEffect, useMemo, useState} from 'react';
import {ArrowDownToLine, ArrowUpRight, Building2, CalendarDays, Database, ExternalLink, Lightbulb, ShieldCheck} from 'lucide-react';
import type {AdditionalData, RegionEconomy, SettlementEconomy} from '../../lib/additional-types';
import {flightOnDate, formatNumber as fmt, money, sectorNames, selectedEconomy, seasonState} from '../../lib/additional-model';
import EconomyMap from './economy-map';

function save(name:string, value:unknown) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'}));
  const a = document.createElement('a'); a.href=url; a.download=name; a.click(); setTimeout(()=>URL.revokeObjectURL(url),1000);
}

export function useSettlements(region:string) {
  const [state,setState] = useState<{region:string;rows:SettlementEconomy[];error:string;loading:boolean}>({region:'',rows:[],error:'',loading:false});
  useEffect(()=>{
    if(region==='all') {setState({region,rows:[],error:'',loading:false});return;}
    const controller=new AbortController();
    setState({region,rows:[],error:'',loading:true});
    fetch(`/additional/regions/${region}.json`,{signal:controller.signal}).then(r=>{if(!r.ok)throw Error();return r.json()})
      .then(rows=>{if(!Array.isArray(rows))throw Error();setState({region,rows:rows as SettlementEconomy[],error:'',loading:false})})
      .catch(e=>{if(e.name!=='AbortError')setState({region,rows:[],error:'Не удалось загрузить населённые пункты.',loading:false});});
    return()=>controller.abort();
  },[region]);
  return state.region===region ? state : {region,rows:[],error:'',loading:region!=='all'};
}

export function EconomyPanel({data,region,onRegion}:{data:AdditionalData;region:string;onRegion:(id:string)=>void}) {
  const [sector,setSector]=useState('all'),[search,setSearch]=useState('');
  const settlements=useSettlements(region);
  const summary=selectedEconomy(data.regions,region,sector);
  const selected=data.regions.find(r=>r.region_id===region);
  const sorted=useMemo(()=>data.regions.map(r=>({region:r,...selectedEconomy([r],r.region_id,sector)}))
    .sort((a,b)=>(b.revenue??-Infinity)-(a.revenue??-Infinity)),[data,sector]);
  const shown=settlements.rows.filter(p=>p.name.toLowerCase().includes(search.toLowerCase())).slice(0,40);
  return <div className="additional-panel">
    <div className="data-toolbar"><label>Территория<select aria-label="Территория экономики" value={region} onChange={e=>onRegion(e.target.value)}><option value="all">82 региона атласа</option>{data.regions.map(r=><option key={r.region_id} value={r.region_id}>{r.name}</option>)}</select></label>
      <label>Отрасль<select aria-label="Отрасль экономики" value={sector} onChange={e=>setSector(e.target.value)}><option value="all">Все отрасли</option>{Object.entries(sectorNames).map(([id,name])=><option key={id} value={id}>{id} · {name}</option>)}</select></label>
      <span className="data-period">Отчётность за {data.financial_year} год</span>
      <button className="text-button" onClick={()=>save(`economy-${region}-${sector}.json`,{year:data.financial_year,region,sector,schema_version:data.schema_version,quality_filter:data.strict_filter,assignment_radius_km:data.assignment_radius_km,summary,regions:sorted.filter(r=>region==='all'||r.region.region_id===region)})}><ArrowDownToLine size={14}/>Скачать выборку</button></div>
    <div className="data-kpis">
      <div><Building2 size={19}/><span>Компании в источнике</span><strong>{fmt(summary.company_rows)}</strong><small>Выбранная территория и отрасль</small></div>
      <div><ShieldCheck size={19}/><span>Прошли фильтр качества</span><strong>{fmt(summary.strict_rows)}</strong><small>Отчёт подан, без выбросов, адрес до дома или улицы</small></div>
      <div><Database size={19}/><span>Из них с выручкой</span><strong>{fmt(summary.revenue_rows)}</strong><small>{summary.strict_rows?`${fmt(summary.revenue_rows/summary.strict_rows*100,1)}% от прошедших фильтр`:'Нет подходящих записей'}</small></div>
      <div><span className="ruble-symbol">₽</span><span>Суммарная выручка</span><strong>{money(summary.revenue)}</strong><small>Только прошедшие фильтр и с заполненной выручкой</small></div>
    </div>
    <p className="data-note">География относится к регистрации юридических лиц. Выручка описывает продажи компаний и не является ВРП или грузопотоком. Фильтр также исключает восстановленные записи и невалидные координаты. {region==='all'&&<>За пределами 82 регионов атласа остаются {fmt(data.summary.outside_atlas_rows)} записей источника, включая федеральные города.</>}</p>
    {!selected&&<EconomyMap regions={data.regions} onRegion={onRegion}/>}
    {selected&&<div className="data-dual"><section className="data-box"><h2>Связь с официальной выгрузкой ФНС</h2><p>Совпало по ИНН <b>{fmt(selected.fns_matched_rows)}</b> из {fmt(selected.company_rows)} записей RFSD региона.</p><p>Среди прошедших фильтр — {fmt(selected.strict_fns_rows)} совпадений. Их бухгалтерский доход: <b>{money(selected.strict_fns_income_rub)}</b>.</p><small>Доход ФНС и выручка RFSD — разные показатели. Суммы двух источников не складываются. Разрез ФНС относится ко всем отраслям региона.</small></section>
      <section className="data-box"><h2><Lightbulb size={17}/> Ночная освещённость</h2><div className="light-years">{selected.lights.map(l=><div key={l.year}><b>{l.year}</b><strong>{fmt(l.mean_raw,2)}</strong><span>среднее исходное значение</span><small>{fmt(l.valid_points)} точек · {fmt(l.zero_points)} нулевых</small></div>)}</div><small>Один пиксель в координате НП; исходная шкала поставщика. Нулевой пиксель не доказывает отсутствие деятельности. Охват — все НП региона, независимо от отрасли.</small></section></div>}
    <section className="table-panel"><div className="table-header"><h2>{selected?'Экономика по отраслям':'Сравнение регионов'}</h2><span className="paper-tag">2025</span></div><div className="table-scroll"><table><thead><tr><th>{selected?'Отрасль':'Регион'}</th><th>Прошли фильтр</th><th>С выручкой</th><th>Выручка</th>{!selected&&<th/>}</tr></thead><tbody>
      {selected ? selected.sectors.filter(s=>sector==='all'||s.sector===sector).map(s=><tr key={s.sector}><td>{sectorNames[s.sector]||s.sector}</td><td>{fmt(s.strict_rows)}</td><td>{fmt(s.strict_revenue_rows)}</td><td>{money(s.strict_revenue_rub)}</td></tr>) : sorted.map(r=><tr key={r.region.region_id}><td>{r.region.name}</td><td>{fmt(r.strict_rows)}</td><td>{fmt(r.revenue_rows)}</td><td>{money(r.revenue)}</td><td><button className="text-button" onClick={()=>onRegion(r.region.region_id)}>Открыть<ArrowUpRight size={13}/></button></td></tr>)}
    </tbody></table></div></section>
    {selected&&<section className="table-panel"><div className="table-header"><h2>Населённые пункты</h2><input className="data-search" aria-label="Поиск в экономическом слое" placeholder="Название населённого пункта" value={search} onChange={e=>setSearch(e.target.value)}/></div>
      <p className="table-note">Компании связаны с ближайшим НП своего региона в радиусе {data.assignment_radius_km} км. Это приближённая привязка адреса регистрации, не расположение производства. Таблица охватывает все отрасли; показаны первые 40 совпадений.</p>
      {settlements.loading?<p className="data-note" role="status">Загружаем населённые пункты…</p>:settlements.error?<p className="data-note" role="alert">{settlements.error}</p>:<div className="table-scroll"><table><thead><tr><th>Населённый пункт</th><th>Жители</th><th>Привязано компаний</th><th>Выручка</th><th>Свет 2023 / 2024</th></tr></thead><tbody>{shown.map(p=><tr key={p.point_id}><td>{p.name}</td><td>{fmt(p.population)}</td><td>{fmt(p.company_rows)}</td><td>{money(p.revenue_rub)}</td><td>{fmt(p.light_2023)} / {fmt(p.light_2024)}</td></tr>)}</tbody></table>{!shown.length&&<p className="data-note">Населённые пункты не найдены.</p>}</div>}
    </section>}
  </div>;
}

export function SeasonsPanel({data}:{data:AdditionalData}) {
  const [routeId,setRouteId]=useState(data.route_seasons[0]?.route_id||'');
  const [year,setYear]=useState(2026),[day,setDay]=useState('2026-03-20'),[tonnes,setTonnes]=useState('10'),[scenario,setScenario]=useState(false);
  const [flightDay,setFlightDay]=useState('2026-11-09');
  const settlements=useSettlements('71800000');
  const routes=[...new Map(data.route_seasons.map(r=>[r.route_id,r])).values()];
  const history=data.route_seasons.filter(r=>r.route_id===routeId).sort((a,b)=>a.season_end_year-b.season_end_year);
  const selected=history.find(r=>r.season_end_year===year);
  const state=selected?seasonState(selected,day,tonnes.trim()?Number(tonnes):NaN,scenario):null;
  const baseline=selected?seasonState(selected,day,tonnes.trim()?Number(tonnes):NaN,false):null;
  const stops=settlements.rows.filter(p=>selected?.stop_ids.includes(p.point_id));
  const flights=data.context.kap_schedule||[];
  const departures=[...new Map(flights.filter(f=>flightOnDate(f,flightDay)===true).map(f=>[[f.flight,f.origin,f.destination,f.departure_local].join('|'),f])).values()];
  const unsupported=flights.filter(f=>flightOnDate(f,flightDay)===null).length;
  return <div className="additional-panel">
    <section className="data-box"><div className="panel-title"><CalendarDays size={22}/><div><h2>Зимники Югры</h2><p>Девять маршрутов · проверенные записи сезонов 2024/25 и 2025/26</p></div></div>
      <div className="data-toolbar"><label className="route-select">Маршрут<select aria-label="Сезонный маршрут" value={routeId} onChange={e=>setRouteId(e.target.value)}>{routes.map(r=><option key={r.route_id} value={r.route_id}>{r.route}</option>)}</select></label><label>Сезон<select aria-label="Год сезона" value={year} onChange={e=>{const y=Number(e.target.value);setYear(y);setDay(`${y}-03-20`);}}><option value={2025}>2024/25</option><option value={2026}>2025/26</option></select></label><label>Дата<input aria-label="Дата поездки по зимнику" type="date" value={day} onChange={e=>setDay(e.target.value)}/></label><label>Масса, т<input aria-label="Масса автомобиля в тоннах" type="number" min="0.1" step="0.5" value={tonnes} onChange={e=>setTonnes(e.target.value)}/></label></div>
      <label className="scenario-toggle"><input type="checkbox" checked={scenario} onChange={e=>setScenario(e.target.checked)}/><span>Сценарий: круглогодичный проезд для выбранной массы</span></label>
      {state&&<div className={`season-state ${state.kind}`} role="status"><strong>{state.label}</strong><p>{state.detail}</p>{scenario&&baseline&&<small>По исходным данным: {baseline.label.toLowerCase()}.</small>}</div>}
      <p className="data-note">Сценарий меняет условие работы выбранной связи. Время поездки, альтернативные пути и число изолированных жителей требуют дорожного графа и здесь не рассчитываются.</p>
      <div className="table-scroll"><table><thead><tr><th>Сезон</th><th>Открытие</th><th>Закрытие</th><th>Между датами</th><th>Ограничение</th><th>Источник</th></tr></thead><tbody>{history.map(r=><tr key={r.season_end_year}><td>{r.season_end_year-1}/{String(r.season_end_year).slice(2)}</td><td>{r.opening_date||'Не установлено'}</td><td>{r.closure_date||`Не установлено на ${r.report_date}`}</td><td>{r.elapsed_days==null?'Нет обеих дат':`${r.elapsed_days} дней`}</td><td>{r.weight_limit_tonnes==null?'Не установлено':`${r.weight_limit_tonnes} т с ${r.restriction_start_date}`}</td><td>{r.source_url?<a className="source-link" href={`${r.source_url}#page=${r.pdf_page}`} target="_blank" rel="noreferrer">Стр. {r.pdf_page}<ExternalLink size={12}/></a>:r.source_file}</td></tr>)}</tbody></table></div>
      <p className="data-note">Интервал — разность дат без включения дня закрытия. Это не количество дней гарантированного проезда: промежуточные перерывы могут отсутствовать в источниках.</p>
    </section>
    <section className="data-box"><h2>Населённые пункты на выбранном маршруте</h2><p>Сопоставлены по названиям и муниципальному району. Эти жители и компании не считаются автоматически зависимыми от единственного пути.</p>
      {settlements.loading?<p role="status">Загружаем данные поселений…</p>:settlements.error?<p role="alert">{settlements.error}</p>:<div className="table-scroll"><table><thead><tr><th>Пункт</th><th>Население</th><th>Привязано компаний</th><th>Выручка 2025</th></tr></thead><tbody>{stops.map(p=><tr key={p.point_id}><td>{p.name}</td><td>{fmt(p.population)}</td><td>{fmt(p.company_rows)}</td><td>{money(p.revenue_rub)}</td></tr>)}</tbody></table>{!stops.length&&<p className="data-note">Нет однозначно сопоставленных населённых пунктов.</p>}</div>}
      {!!selected?.unresolved_stops.length&&<p className="data-note">Не сопоставлены: {selected.unresolved_stops.join(', ')}.</p>}
    </section>
    <section className="data-box"><div className="panel-title"><CalendarDays size={22}/><div><h2>Авиация Камчатки по календарю</h2><p>Опубликованное зимнее расписание КАП · 26.10.2026–26.03.2027</p></div></div>
      <div className="data-toolbar"><label>Дата отправления<input aria-label="Дата авиарейсов" type="date" value={flightDay} onChange={e=>setFlightDay(e.target.value)}/></label><span className="data-period">{departures.length} сегментов в расписании</span></div>
      <div className="table-scroll"><table><thead><tr><th>Рейс</th><th>Откуда</th><th>Куда</th><th>Местное время</th></tr></thead><tbody>{departures.map((r,i)=><tr key={i}><td>{r.flight}</td><td>{r.origin}</td><td>{r.destination}</td><td>{r.departure_local} → {r.arrival_local}</td></tr>)}</tbody></table>{!departures.length&&<p className="data-note">В подключённом расписании нет отправлений на выбранную дату.</p>}</div>
      <p className="data-note">Расписание не подтверждает фактическое выполнение. {unsupported>0&&`${unsupported} строк с нераспознанными условиями не включены. `}<a href="https://aokap.ru/uslugi/regulyarnye-perevozki/raspisanie-zima/" className="source-link" target="_blank" rel="noreferrer">Расписание перевозчика<ExternalLink size={12}/></a></p>
    </section>
  </div>;
}

export function SourceCatalog({data}:{data:AdditionalData}) {
  return <section className="additional-panel"><div className="section-heading"><div><h2>Подключённые источники</h2><p>Периоды и ограничения сохраняются вместе с данными</p></div></div><div className="source-catalog">{data.sources.map(s=><article className="data-box" key={s.id}><span className="paper-tag">{s.period}</span><h3>{s.title}</h3><p>{s.note}</p><span className="data-source-count">{fmt(s.rows)} строк в основной таблице</span>{s.url&&<a href={s.url} target="_blank" rel="noreferrer" className="source-link">Источник<ExternalLink size={12}/></a>}</article>)}</div>
    <div className="data-box"><h2>Данные для дальнейших расчётов</h2><p>Северный завоз, события МЧС и обследования потока загружены с исходными единицами и происхождением. Пространственная привязка всех объектов и проверка сопоставимости периодов ещё требуются.</p><p><b>Экономическая доступность: {data.economic_access.rows?'рассчитана в базе данных':'ещё не рассчитана'}.</b> {data.economic_access.rows?'Индекс рассчитан по сохранённому времени поездок; карта выше показывает исходные экономические показатели.':'В этой сборке отсутствуют расчёты времени поездок по транспортному графу. Экономический слой пока не меняет Hansen и оценки эффекта новых дорог.'}</p><button className="text-button" onClick={()=>save('transport-context.json',data.context)}><ArrowDownToLine size={14}/>Скачать подключённые транспортные таблицы</button></div>
  </section>;
}
