import {chromium} from '../../frontend/node_modules/@playwright/test/index.mjs';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
const data=JSON.parse(await readFile(new URL('./services.json',import.meta.url),'utf8'));
const b=await chromium.launch();const p=await b.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:2});
await p.goto(new URL('../plexus-deck.html',import.meta.url).href+'?static#4');await p.waitForSelector('html[data-ready="true"]',{timeout:90000});await p.addStyleTag({content:'.deck-scenes{visibility:hidden}'});
const meta=await p.evaluate(async d=>{
 const m=window.__plexusDemoMap;m.stop();for(const l of m.getStyle().layers)if(l.id.startsWith('demo-'))m.setLayoutProperty(l.id,'visibility','none');
 const add=(id,data,type,paint)=>{m.addSource(id,{type:'geojson',data});m.addLayer({id,type,source:id,paint})};
 add('svc-area',d.municipality,'fill',{'fill-color':'#0064df','fill-opacity':.05});add('svc-white',d.municipality,'line',{'line-color':'#fff','line-width':6});add('svc-boundary',d.municipality,'line',{'line-color':'#0064df','line-width':2.5});
 const points=d.municipality.geometry.coordinates.flat(d.municipality.geometry.type==='MultiPolygon'?2:1);
 m.fitBounds([[Math.min(...points.map(p=>p[0])),Math.min(...points.map(p=>p[1]))],[Math.max(...points.map(p=>p[0])),Math.max(...points.map(p=>p[1]))]],{duration:0,padding:{top:170,bottom:150,left:90,right:90}});
 for(const s of d.services){add('svc-'+s.id,{type:'FeatureCollection',features:s.points.map(p=>({type:'Feature',properties:{within:p.within},geometry:{type:'Point',coordinates:p.xy}}))},'circle',{'circle-color':['case',['get','within'],'#00a27a','#e6533f'],'circle-radius':s.id==='N01'?7:3.5,'circle-stroke-color':'white','circle-stroke-width':s.id==='N01'?2:1});m.setLayoutProperty('svc-'+s.id,'visibility','none')}
 await new Promise(r=>{m.once('idle',r);m.triggerRepaint()});const rect=m.getCanvas().getBoundingClientRect();const groups=new Map();for(const p of d.services[1].points){const key=Math.floor(p.xy[0]/.04)+':'+Math.floor(p.xy[1]/.04);if(!groups.has(key))groups.set(key,[]);groups.get(key).push(p.xy)}const cluster=[...groups.values()].sort((a,b)=>b.length-a.length)[0];const center=cluster.reduce((a,p)=>[a[0]+p[0]/cluster.length,a[1]+p[1]/cluster.length],[0,0]);const xy=m.project(center);return {rect:{x:rect.x,y:rect.y,width:rect.width,height:rect.height},focus:[xy.x/m.getCanvas().clientWidth,xy.y/m.getCanvas().clientHeight]};
},data);
await mkdir(new URL('./service-frames/',import.meta.url),{recursive:true});
for(const state of ['neutral',...data.services.map(s=>s.id)]){
 await p.evaluate(async state=>{const m=window.__plexusDemoMap;for(const id of ['N01','N04','N09'])m.setLayoutProperty('svc-'+id,'visibility',id===state?'visible':'none');await new Promise(r=>{m.once('idle',r);m.triggerRepaint()})},state);
 await p.screenshot({path:new URL('./service-frames/'+state+'.png',import.meta.url).pathname,clip:meta.rect});
}
await writeFile(new URL('./service-frames/metadata.json',import.meta.url),JSON.stringify(meta));
await b.close();console.log('Service maps rendered');
