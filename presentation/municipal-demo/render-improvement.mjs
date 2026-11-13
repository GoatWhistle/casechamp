import {chromium} from '../../frontend/node_modules/@playwright/test/index.mjs';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
const data=JSON.parse(await readFile(new URL('./improvement.json',import.meta.url),'utf8'));
const b=await chromium.launch();
const p=await b.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:2});
await p.goto(new URL('../plexus-deck.html',import.meta.url).href+'?static#4');
await p.waitForSelector('html[data-ready="true"]',{timeout:90000});
await p.addStyleTag({content:'.deck-scenes{visibility:hidden}'});
const meta=await p.evaluate(async d=>{
 const m=window.__plexusDemoMap;m.stop();
 for(const l of m.getStyle().layers)if(l.id.startsWith('demo-'))m.setLayoutProperty(l.id,'visibility','none');
 const add=(id,data,type,paint)=>{m.addSource(id,{type:'geojson',data});m.addLayer({id,source:id,type,paint,layout:type==='line'?{'line-cap':'round','line-join':'round'}:{}})};
 add('im-area',d.municipality,'fill',{'fill-color':'#0075ef','fill-opacity':.08});
 add('im-halo',d.municipality,'line',{'line-color':'#fff','line-width':7});
 add('im-border',d.municipality,'line',{'line-color':'#0064df','line-width':2.5});
 add('im-road-halo',d.road,'line',{'line-color':'#fff','line-width':10});
 add('im-road',d.road,'line',{'line-color':'#e74732','line-width':5});
 const pts=d.municipality.geometry.coordinates.flat(d.municipality.geometry.type==='MultiPolygon'?2:1);
 m.fitBounds([[Math.min(...pts.map(p=>p[0])),Math.min(...pts.map(p=>p[1]))],[Math.max(...pts.map(p=>p[0])),Math.max(...pts.map(p=>p[1]))]],{duration:0,padding:{top:40,bottom:390,left:100,right:100}});
 const coords=d.road.features.flatMap(f=>f.geometry.coordinates);const xy=coords[Math.floor(coords.length/2)];
 add('im-pin',{type:'Feature',properties:{},geometry:{type:'Point',coordinates:xy}},'circle',{'circle-color':'#e74732','circle-radius':9,'circle-stroke-color':'white','circle-stroke-width':3});
 await new Promise(r=>{m.once('idle',r);m.triggerRepaint()});
 const pt=m.project(xy),canvas=m.getCanvas(),r=canvas.getBoundingClientRect();
 return {center:[pt.x/canvas.clientWidth,pt.y/canvas.clientHeight],rect:{x:r.x,y:r.y,width:r.width,height:r.height}};
},data);
await mkdir(new URL('./improvement-frames/',import.meta.url),{recursive:true});
for(const state of ['neutral','before','after']){
 await p.evaluate(async state=>{const m=window.__plexusDemoMap;for(const id of ['im-road-halo','im-road','im-pin'])m.setLayoutProperty(id,'visibility',state==='neutral'?'none':'visible');await new Promise(r=>{m.once('idle',r);m.triggerRepaint()})},state);
 if(state==='after')await p.evaluate(async()=>{const m=window.__plexusDemoMap;m.setPaintProperty('im-road','line-color','#00a875');m.setPaintProperty('im-road','line-width',7);m.setPaintProperty('im-pin','circle-color','#00a875');await new Promise(r=>{m.once('idle',r);m.triggerRepaint()})});
 await p.screenshot({path:new URL('./improvement-frames/'+state+'.png',import.meta.url).pathname,clip:meta.rect});
}
await writeFile(new URL('./improvement-frames/metadata.json',import.meta.url),JSON.stringify(meta));
await b.close();console.log('Municipality frames rendered');
