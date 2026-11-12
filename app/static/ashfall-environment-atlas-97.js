/* ASHFALL 97 — shared high-resolution illustrated environmental atlases.
   Same original artwork used in both settlement and wilderness.
   Async load, camera/world-space drawing, deterministic placement, graceful fallback. */
(function(){
"use strict";
const names=["forest","ruins","rockfield"],images=new Map();
const status={loaded:0,failed:0};
for(const name of names){
 const img=new Image();img.decoding="async";
 img.onload=()=>{status.loaded++;try{if(typeof window.draw==="function")window.draw()}catch{}};
 img.onerror=()=>{status.failed++;console.warn("ASHFALL 97 atlas missing:",name)};
 img.src="/static/ashfall-art/environment-"+name+"-97.svg?v=1";
 images.set(name,img);
}
const settings={enabled:true,settlement:true,wilderness:true,opacity:.9};
function render(ctx,mode){
 if(!settings.enabled||!settings[mode])return;
 const places=mode==="settlement"?
 [["forest",-1230,-1000,700,440],["forest",750,-950,650,406],["ruins",-1180,630,600,375],["rockfield",850,600,650,406]]:
 [["forest",-1600,-1200,850,531],["forest",900,-1250,850,531],["ruins",-1550,800,800,500],["rockfield",1000,800,850,531]];
 ctx.save();ctx.globalAlpha=settings.opacity;ctx.imageSmoothingEnabled=true;ctx.imageSmoothingQuality="high";
 for(const [name,x,y,w,h] of places){
  const img=images.get(name);
  if(img?.complete&&img.naturalWidth)ctx.drawImage(img,x,y,w,h);
 }
 ctx.restore();
}
window.ASHFALL_ENV_ATLAS_97={render,settings,status:()=>({...status,total:names.length})};
})();