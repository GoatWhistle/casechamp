'use client';
import {useEffect, useMemo, useState} from 'react';
import type {RegionEconomy} from '../../lib/additional-types';
import {formatNumber, money} from '../../lib/additional-model';

type Shape={id:string;name:string;path:string;center:number[]};
const colors=['#edf1e7','#d3dfc7','#adc49b','#7d9f67','#426c39'];
export default function EconomyMap({regions,onRegion}:{regions:RegionEconomy[];onRegion:(id:string)=>void}) {
  const [shapes,setShapes]=useState<Shape[]>([]),[error,setError]=useState(''),[metric,setMetric]=useState('companies'),[hover,setHover]=useState('71800000');
  useEffect(()=>{let active=true;fetch('/geo/region-paths.json').then(r=>{if(!r.ok)throw Error();return r.json()}).then(d=>{if(!d || typeof d!=='object' || !('regions' in d) || !Array.isArray(d.regions))throw Error();if(active)setShapes(d.regions as Shape[])}).catch(()=>{if(active)setError('Карта недоступна. Выбор региона доступен в таблице ниже.')});return()=>{active=false}},[]);
  const values=useMemo(()=>new Map(regions.map(r=>[r.region_id,metric==='companies'?r.strict_rows:metric==='revenue'?r.strict_revenue_rub:r.lights.find(l=>l.year===2024)?.mean_raw??null])),[regions,metric]);
  const known=[...values.values()].filter((v):v is number=>v!=null).sort((a,b)=>a-b);
  const breaks=[.2,.4,.6,.8].map(q=>known[Math.floor((known.length-1)*q)]??0);
  const color=(v:number|null|undefined)=>v==null?'url(#economic-unknown)':colors[breaks.filter(b=>v>b).length];
  const selected=regions.find(r=>r.region_id===hover),value=values.get(hover);
  const unit=metric==='revenue'?'Выручка, млрд ₽':metric==='light'?'Освещённость, исходная шкала':'Компании после фильтра';
  const show=(n:number|null|undefined)=>metric==='revenue'?money(n):formatNumber(n,metric==='light'?2:0);
  return <section className="economic-map-box"><div className="data-toolbar"><label>Слой карты<select aria-label="Экономический слой карты" value={metric} onChange={e=>setMetric(e.target.value)}><option value="companies">Компании · 2025</option><option value="revenue">Выручка · 2025</option><option value="light">Освещённость · 2024</option></select></label><span className="data-period">Все отрасли · нажмите на регион</span></div>
    <div className="economic-map-body"><div>{error?<p role="alert" className="data-note">{error}</p>:<svg viewBox="0 0 1000 640" aria-label="Экономические данные по регионам" className="economic-svg"><defs><pattern id="economic-unknown" width="7" height="7" patternUnits="userSpaceOnUse"><rect width="7" height="7" fill="#e9e9e3"/><path d="M0 7L7 0" stroke="#cbcdc4" strokeWidth=".6"/></pattern></defs>{shapes.map(s=><path key={s.id} d={s.path} fillRule="evenodd" fill={color(values.get(s.id))} stroke={s.id===hover?'#315d30':'#a9b6a2'} strokeWidth={s.id===hover?2:0.6} role="button" tabIndex={values.has(s.id)?0:-1} aria-label={`${s.name}: ${show(values.get(s.id))}`} onMouseEnter={()=>setHover(s.id)} onFocus={()=>setHover(s.id)} onClick={()=>values.has(s.id)&&onRegion(s.id)} onKeyDown={e=>{if((e.key==='Enter'||e.key===' ')&&values.has(s.id)){e.preventDefault();onRegion(s.id)}}}><title>{s.name}: {show(values.get(s.id))}</title></path>)}</svg>}</div>
      <aside><span className="eyebrow">{unit}</span><h3>{selected?.name||shapes.find(s=>s.id===hover)?.name||'Выберите регион'}</h3><strong>{show(value)}</strong><p>{selected?`Выручка заполнена у ${formatNumber(selected.strict_revenue_rows)} из ${formatNumber(selected.strict_rows)} компаний после фильтра.`:'Территория вне текущей выборки.'}</p>{selected&&<button className="primary-button" onClick={()=>onRegion(selected.region_id)}>Открыть данные региона</button>}</aside></div>
    <div className="economic-legend"><span>Пять групп по значениям регионов</span>{colors.map((c,i)=><span key={c}><i style={{background:c}}/>{i===0?'Ниже':i===4?'Выше':''}</span>)}<span>Штриховка — вне выборки / нет данных</span></div>
    <p className="data-note">Карта показывает все отрасли. Освещённость — среднее по точкам НП, не показатель ВРП. Границы из снимка 2013 года; Крым доступен через список и таблицу. © OpenStreetMap contributors · Click That Hood.</p>
  </section>;
}
