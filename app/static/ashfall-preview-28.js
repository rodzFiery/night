/* ASHFALL 28 — Interactive architectural tier preview.
   Preview only: never modifies the live building, economy, or construction queue. */
(function(){
"use strict";
const tiers=[0,5,15,30,50],cache=new Map();
let current=null,requestId=0;
function image(key){
 if(!cache.has(key)){
  const img=new Image();img.decoding="async";
  img.src="/static/ashfall-art/"+encodeURIComponent(key)+".svg?v="+(key==="hq"?3:2);
  cache.set(key,img);
 }
 return cache.get(key);
}
function render(){
 if(!current)return;
 const canvas=document.getElementById("afEvolutionCanvas");
 const status=document.getElementById("afPreviewStatus");
 if(!canvas||!status)return;
 const ctx=canvas.getContext("2d");
 if(!ctx)return;
 const {key,level,actual}=current,img=image(key);
 const dpr=Math.min(2,Math.max(1,window.devicePixelRatio||1));
 const w=340,h=266;
 if(canvas.width!==Math.round(w*dpr)||canvas.height!==Math.round(h*dpr)){
  canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);
 }
 ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,w,h);
 ctx.imageSmoothingEnabled=true;ctx.imageSmoothingQuality="high";
 if(img.complete&&img.naturalWidth){
  ctx.drawImage(img,0,0,w,h);
  window.ASHFALL_ART_EVOLUTION?.draw(ctx,0,0,w,h,key,level);
  status.textContent="PREVIEW LEVEL "+level+(level===actual?" · CURRENT":" · NOT APPLIED");
 }else{
  ctx.fillStyle="#24343a";ctx.fillRect(0,0,w,h);
  status.textContent="LOADING ARCHITECTURAL ART";
  const token=++requestId;
  img.addEventListener("load",()=>{if(token===requestId)render()},{once:true});
  img.addEventListener("error",()=>{if(token===requestId)status.textContent="ART PREVIEW UNAVAILABLE"},{once:true});
 }
 for(const button of document.querySelectorAll("[data-af-tier]")){
  const tier=Number(button.dataset.afTier);
  button.setAttribute("aria-pressed",String(tier===level));
  button.classList.toggle("selected",tier===level);
 }
}
function select(tier){
 if(!current||!tiers.includes(tier))return;
 current.level=tier;render();
}
function show(key,actual){
 if(!["hq","farm","lumber","salvage","fuel","barracks"].includes(key))return;
 const safeActual=Math.max(0,Math.min(55,Number(actual)||0));
 const changed=!current||current.key!==key||current.actual!==safeActual;
 if(changed)current={key,actual:safeActual,level:safeActual};
 render();
}
window.ASHFALL_ARCH_PREVIEW={show,select,tiers,reset:()=>{current=null;requestId++}};
})();