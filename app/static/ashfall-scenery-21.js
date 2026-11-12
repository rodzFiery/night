/* ASHFALL 22 — Depth-aware illustrated environment compositor.
   Stable visual ordering, contact shadows and atmospheric depth.
   Never changes simulation state, hit targets or building positions. */
(function(){
"use strict";
const names=["ruin","pines","scrap"],images=new Map();
const settings={enabled:true,density:1,shadows:true,atmosphere:true};
let loaded=0,failed=0;
for(const name of names){
 const img=new Image();img.decoding="async";
 img.onload=()=>{loaded++;try{if(typeof draw==="function")draw()}catch{}};
 img.onerror=()=>{failed++;console.warn("ASHFALL scenery unavailable:",name)};
 img.src="/static/ashfall-scenery/"+name+".svg?v=1";
 images.set(name,img);
}
function noise(i){let n=(Math.imul(i+12345,2654435761)>>>0);n^=n>>>16;n=Math.imul(n,2246822519)>>>0;n^=n>>>13;return(n>>>0)/4294967296}
function entries(){
 if(!settings.enabled)return [];
 const count=Math.max(0,Math.min(24,Math.round(14*settings.density))),items=[];
 for(let i=0;i<count;i++){
  const angle=(i+.25+noise(i)*.45)*Math.PI*2/count;
  const radius=920+noise(i+39)*490;
  const x=Math.cos(angle)*radius,y=Math.sin(angle)*radius*.54;
  const name=names[i%names.length],img=images.get(name);
  if(!img||!img.complete||!img.naturalWidth)continue;
  const size=.72+noise(i+77)*.43,w=265*size,h=199*size;
  items.push({id:i,x,y,w,h,img,opacity:.82+noise(i+14)*.18});
 }
 return items;
}
function paint(ctx,item){
 ctx.save();
 const {x,y,w,h,img,opacity}=item;
 if(settings.shadows){
  ctx.fillStyle="rgba(6,17,18,.29)";
  ctx.beginPath();ctx.ellipse(x+17,y+7,w*.42,h*.11,-.07,0,Math.PI*2);ctx.fill();
 }
 ctx.globalAlpha=opacity;
 ctx.imageSmoothingEnabled=true;ctx.imageSmoothingQuality="high";
 ctx.drawImage(img,x-w/2,y-h*.88,w,h);
 if(settings.atmosphere){
  const fog=ctx.createLinearGradient(x,y-h*.75,x,y+12);
  fog.addColorStop(0,"rgba(161,176,164,.10)");
  fog.addColorStop(.6,"rgba(161,176,164,.015)");
  fog.addColorStop(1,"rgba(161,176,164,0)");
  ctx.globalCompositeOperation="source-atop";
  ctx.fillStyle=fog;ctx.fillRect(x-w/2,y-h*.88,w,h);
 }
 ctx.restore();
}
function render(ctx,pass="all"){
 const items=entries().filter(e=>pass==="all"||(pass==="back"?e.y<0:e.y>=0));
 items.sort((a,b)=>a.y-b.y||a.id-b.id);
 for(const item of items)paint(ctx,item);
}
window.ASHFALL_SCENERY={render,entries,paint,settings,status:()=>({loaded,failed,total:names.length})};
})();