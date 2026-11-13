const indexMapCache=new Image();
indexMapCache.src=indexMapFrame;
indexMapCache.decode().catch(()=>{});
const indexTransition=iye.beats[1].run;
iye.beats[1].run=async function(context){
  const map=context.part('map');
  await indexMapCache.decode();
  const frame=indexMapCache.cloneNode();
  frame.className='index-map-frame';
  frame.alt='';
  map.querySelector('svg').style.display='none';
  map.append(frame);
  await indexTransition(context);
};
