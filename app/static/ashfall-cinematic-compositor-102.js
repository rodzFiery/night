/* ASHFALL 102 — Cinematic compositing pass.
   Presentation-only overlay: independent DPR-aware canvas, capped frame rate,
   reduced-motion aware, no interaction interception, no gameplay mutations. */
(function(){
"use strict";
let overlay,ctx,width=0,height=0,dpr=1,active=true,last=0,frame=0;
const motion=window.matchMedia?.("(prefers-reduced-motion: reduce)");
const particles=Array.from({length:46},(_,i)=>({
 x:((i*127.7)%1000)/1000,y:((i*61.9)%1000)/1000,
 speed:.015+(i%7)*.004,radius:.55+(i%4)*.38,phase:i*1.61,
 alpha:.11+(i%5)*.055
}));
function resize(){
 if(!overlay)return;
 width=window.innerWidth;height=window.innerHeight;
 dpr=Math.min(window.devicePixelRatio||1,1.7);
 overlay.width=Math.round(width*dpr);overlay.height=Math.round(height*dpr);
 overlay.style.width=width+"px";overlay.style.height=height+"px";
 ctx.setTransform(dpr,0,0,dpr,0,0);
}
function mode(){return document.getElementById("settlement")?.classList.contains("active")?"settlement":"wilderness"}
function render(ts){
 if(!active)return;
 frame=requestAnimationFrame(render);
 if(document.hidden||!width||ts-last<40)return;
 last=ts;
 const w=width,h=height,t=ts*.001;
 ctx.clearRect(0,0,w,h);
 // Screen-space lens composition. Atmospheric wash intentionally subtle.
 const horizon=ctx.createLinearGradient(0,0,w,h);
 horizon.addColorStop(0,"rgba(242,171,105,.075)");
 horizon.addColorStop(.35,"rgba(62,77,80,0)");
 horizon.addColorStop(1,"rgba(30,61,83,.095)");
 ctx.fillStyle=horizon;ctx.fillRect(0,0,w,h);
 if(mode()==="settlement"&&!motion?.matches){
  // Sparse sunlit dust: screen-space so camera interaction remains smooth.
  for(const p of particles){
   const x=(p.x*w+Math.sin(t*.25+p.phase)*35+w)%w;
   const y=((p.y*h-t*p.speed*24)%h+h)%h;
   ctx.fillStyle="rgba(255,208,145,"+p.alpha+")";
   ctx.beginPath();ctx.arc(x,y,p.radius,0,Math.PI*2);ctx.fill();
  }
  const beam=ctx.createLinearGradient(0,0,w*.58,h);
  beam.addColorStop(0,"rgba(255,207,133,.055)");
  beam.addColorStop(.4,"rgba(255,207,133,.015)");
  beam.addColorStop(1,"rgba(255,207,133,0)");
  ctx.save();ctx.translate(w*.25,0);ctx.transform(1,-.08,-.38,1,0,0);
  ctx.fillStyle=beam;ctx.fillRect(0,0,w*.42,h);ctx.restore();
 }
 const vignette=ctx.createRadialGradient(w*.5,h*.43,Math.min(w,h)*.22,w*.5,h*.5,Math.max(w,h)*.78);
 vignette.addColorStop(0,"rgba(4,9,12,0)");
 vignette.addColorStop(.7,"rgba(4,9,12,.03)");
 vignette.addColorStop(1,"rgba(4,9,12,.28)");
 ctx.fillStyle=vignette;ctx.fillRect(0,0,w,h);
}
function init(){
 overlay=document.createElement("canvas");overlay.id="ashfall-cinematic-compositor";
 overlay.setAttribute("aria-hidden","true");
 Object.assign(overlay.style,{position:"fixed",inset:"0",zIndex:"2",pointerEvents:"none",display:"block"});
 document.body.appendChild(overlay);ctx=overlay.getContext("2d",{alpha:true});
 if(!ctx){overlay.remove();return}
 resize();window.addEventListener("resize",resize,{passive:true});
 document.addEventListener("visibilitychange",()=>{if(!document.hidden)last=0});
 frame=requestAnimationFrame(render);
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init,{once:true});else init();
})();