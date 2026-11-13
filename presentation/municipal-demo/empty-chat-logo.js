let emptyLogoScheduled=false;
function syncEmptyChatLogo(){
 emptyLogoScheduled=false;
 const mark=document.querySelector('.deck-band-mark');
 if(!mark)return;
 for(const panel of document.querySelectorAll('.deck-product aside:has(._empty_8m9lo_58)')){
  if(panel.querySelector('.demo-empty-logo'))continue;
  const logo=document.createElement('div');logo.className='demo-empty-logo';logo.setAttribute('aria-label','plexus');
  const brand=mark.cloneNode(true);brand.removeAttribute('class');logo.append(brand);panel.append(logo);
 }
}
new MutationObserver(()=>{if(!emptyLogoScheduled){emptyLogoScheduled=true;requestAnimationFrame(syncEmptyChatLogo)}}).observe(document.documentElement,{childList:true,subtree:true});
requestAnimationFrame(syncEmptyChatLogo);
