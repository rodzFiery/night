/* ASHFALL 13 — Asset-backed architectural art.
   Six original SVG sprite assets; cached, non-blocking, progressive enhancement.
   The existing Canvas geometry remains the fallback when an asset cannot load. */
(function(){
"use strict";
const keys=["hq","farm","lumber","salvage","fuel","barracks"];
const sprites=new Map();
const config={enabled:true,scale:1,glow:true};
let loaded=0,failed=0;
for(const key of keys){
 const img=new Image();
 img.decoding="async";
 img.onload=()=>{loaded++;try{if(typeof draw==="function")draw()}catch{}};
 img.onerror=()=>{failed++;console.warn("ASHFALL art asset unavailable:",key)};
 img.src="/static/ashfall-art/"+key+".svg?v=1";
 sprites.set(key,img);
}
function render(ctx,pos,b,key,level,constructing){
 if(!config.enabled)return false;
 const img=sprites.get(key);
 if(!img||!img.complete||!img.naturalWidth)return false;
 const size=Math.min(1.15,Math.max(.77,.83+Math.min(level,55)*.005))*config.scale;
 const width=340*size,height=266*size;
 // Existing building position is the center of its roof.
 // Offset sprite downward to align the illustrated plinth with the footprint.
 const left=pos.x-width/2,top=pos.y-height*.73;
 ctx.save();
 if(config.glow&&level>30){
  const strength=Math.min(28,8+(level-30)*.7);
  ctx.shadowColor="#a98aff";ctx.shadowBlur=strength;
 }
 ctx.drawImage(img,left,top,width,height);
 ctx.shadowBlur=0;
 if(constructing){
  ctx.strokeStyle="#f1c083";ctx.lineWidth=2;
  ctx.setLineDash([7,5]);
  ctx.strokeRect(left+width*.13,top+height*.21,width*.74,height*.69);
  ctx.setLineDash([]);
 }
 ctx.restore();
 return true;
}
window.ASHFALL_ART={render,config,status:()=>({loaded,failed,total:keys.length})};
})();