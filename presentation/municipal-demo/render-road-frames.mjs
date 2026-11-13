import {chromium} from '../../frontend/node_modules/@playwright/test/index.mjs';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
const roads=JSON.parse(await readFile(new URL('./roads.json',import.meta.url),'utf8'));
const browser=await chromium.launch();
const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:2});
await page.goto(new URL('../plexus-deck.html',import.meta.url).href+'?static#5');
await page.waitForSelector('html[data-ready="true"]',{timeout:90000});
await page.addStyleTag({content:'.deck-scenes{visibility:hidden}'});
const metadata=await page.evaluate(async roads=>{
 const m=window.__plexusDemoMap;m.stop();
 m.fitBounds([[41.70,44.90],[42.06,45.15]],{duration:0,padding:{top:70,bottom:70,left:70,right:70}});
 if(!m.getSource('demo-roads')){m.addSource('demo-roads',{type:'geojson',data:roads});m.addLayer({id:'demo-roads',type:'line',source:'demo-roads',paint:{'line-color':'#788d88','line-width':3,'line-opacity':.7}});}
 for(const id of ['demo-closed','demo-critical','demo-wave','demo-social'])if(m.getLayer(id))m.removeLayer(id);
 for(const id of ['demo-municipalities','demo-boundaries'])if(m.getLayer(id))m.setLayoutProperty(id,'visibility','none');
 const longest=roads.features.reduce((a,b)=>a.geometry.coordinates.length>b.geometry.coordinates.length?a:b);
 const coords=longest.geometry.coordinates;
 const selected={...longest,geometry:{type:'LineString',coordinates:coords.slice(Math.floor(coords.length*.48),Math.floor(coords.length*.78))}};
 const mid=selected.geometry.coordinates[Math.floor(selected.geometry.coordinates.length/2)];
 const geo=features=>({type:'FeatureCollection',features});
 const layer=(id,data,paint,type='line')=>{m.addSource(id,{type:'geojson',data});m.addLayer({id,type,source:id,paint,layout:type==='line'?{'line-cap':'round','line-join':'round'}:{}})};
 layer('film-selected',geo([selected]),{'line-color':'#fff','line-width':13});
 layer('film-lane-a',geo([selected]),{'line-color':'#008576','line-width':4,'line-offset':-3});
 layer('film-lane-b',geo([selected]),{'line-color':'#008576','line-width':4,'line-offset':3});
 const affected=roads.features.map(f=>{const distance=Math.min(...f.geometry.coordinates.map(p=>Math.hypot((p[0]-mid[0])*.71,p[1]-mid[1])));return {...f,properties:{...f.properties,distance}}}).filter(f=>f.properties.distance<.065);
 layer('film-effect',geo(affected),{'line-color':['interpolate',['linear'],['get','distance'],0,'#d93e29',.025,'#e98431',.065,'#e5b34a'],'line-width':4,'line-opacity':0});
 m.moveLayer('film-selected');m.moveLayer('film-lane-a');m.moveLayer('film-lane-b');
 const indexes=[0,Math.floor(selected.geometry.coordinates.length/2),selected.geometry.coordinates.length-1];
 layer('film-points',geo(indexes.map(i=>({type:'Feature',properties:{},geometry:{type:'Point',coordinates:selected.geometry.coordinates[i]}}))),{'circle-color':'#fff','circle-radius':8,'circle-stroke-color':'#d93e29','circle-stroke-width':3,'circle-opacity':0,'circle-stroke-opacity':0},'circle');
 window.__filmMap=m;
 await new Promise(resolve=>m.once('idle',resolve));
 const center=m.project(mid);const rect=m.getCanvas().getBoundingClientRect();
 return {center:[center.x/m.getCanvas().clientWidth,center.y/m.getCanvas().clientHeight],rect:{x:rect.x,y:rect.y,width:rect.width,height:rect.height},road:longest.properties.name};
},roads);
await mkdir(new URL('./road-frames/',import.meta.url),{recursive:true});
for(const state of ['before','closed','effect','critical']){
 await page.evaluate(async state=>{const m=window.__filmMap;
 if(state==='closed'){m.setPaintProperty('film-lane-b','line-color','#d93e29');m.setPaintProperty('film-lane-b','line-dasharray',[1,1]);}
 if(state==='effect')m.setPaintProperty('film-effect','line-opacity',.95);
 if(state==='critical'){m.setPaintProperty('film-points','circle-opacity',1);m.setPaintProperty('film-points','circle-stroke-opacity',1);}
 await new Promise(resolve=>{m.once('idle',resolve);m.triggerRepaint()});
 },state);
 await page.screenshot({path:new URL('./road-frames/'+state+'.png',import.meta.url).pathname,clip:metadata.rect});
}
await writeFile(new URL('./road-frames/metadata.json',import.meta.url),JSON.stringify(metadata,null,2));
await browser.close();console.log(metadata);
