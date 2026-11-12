/* ASHFALL 21 — Illustrated scenery pass.
   Deterministic positions, asynchronous assets, fallback-safe, visual-only.
   Props are placed outside the main building cluster to avoid hit-target obstruction. */
(function(){
"use strict";
const names=["ruin","pines","scrap"],images=new Map();
const settings={enabled:true,density:1};
let loaded=0,failed=0;
for(const name of names){
 const img=new Image();img.decoding="async";
 img.onload=()=>{loaded++;try{if(typeof draw==="function")draw()}catch{}};
 img.onerror=()=>{failed++;console.warn("ASHFALL scenery unavailable:",name)};
 img.src="/static/ashfall-scenery/"+name+".svg?v=1";
 images.set(name,img);
}
function noise(i){let n=(Math.imul(i+12345,2654435761)>>>0);n^=n>>>16;n=Math.imul(n,2246822519)>>>0;n^=n>>>13;return(n>>>0)/4294967296}
function render(ctx){
 if(!settings.enabled)return;
 const count=Math.max(0,Math.min(24,Math.round(14*settings.density)));
 // World-space scenery stays outside the central settlement's active buildings.
 for(let i=0;i<count;i++){
  const angle=(i+.25+noise(i)*.45)*Math.PI*2/count;
  const radius=920+noise(i+39)*490;
  const x=Math.cos(angle)*radius,y=Math.sin(angle)*radius*.54;
  const name=names[i%names.length],img=images.get(name);
  if(!img||!img.complete||!img.naturalWidth)continue;
  const size=.72+noise(i+77)*.43,w=265*size,h=199*size;
  ctx.save();
  ctx.globalAlpha=.82+noise(i+14)*.18;
  ctx.imageSmoothingEnabled=true;ctx.imageSmoothingQuality="high";
  ctx.drawImage(img,x-w/2,y-h*.88,w,h);
  ctx.restore();
 }
}
window.ASHFALL_SCENERY={render,settings,status:()=>({loaded,failed,total:names.length})};
})();
