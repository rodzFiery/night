/* ASHFALL 114 — optional real-time rendering telemetry.
   Press Ctrl+Shift+F to toggle. No dependencies or gameplay mutations.
   Metrics measure actual frame cadence and artwork streaming, not estimates. */
(function(){
"use strict";
let visible=false,frameCount=0,last=performance.now(),fps=0;
const samples=[];
const root=document.createElement("aside");
root.id="af-performance-hud";
root.hidden=true;
root.setAttribute("role","status");
root.setAttribute("aria-label","ASHFALL rendering diagnostics");
root.style.cssText="position:fixed;right:14px;bottom:14px;z-index:99999;width:260px;max-width:calc(100vw - 28px);padding:14px 16px;border:1px solid #5d7779;border-radius:10px;background:rgba(8,17,22,.94);box-shadow:0 12px 36px #0009;color:#d7e9e6;font:12px/1.55 Consolas,monospace;pointer-events:none;white-space:pre-line";
function frame(now){
 if(!visible)return;
 frameCount++;
 const elapsed=now-last;
 if(elapsed>=1000){
  fps=frameCount*1000/elapsed;frameCount=0;last=now;
  samples.push(fps);if(samples.length>30)samples.shift();
  const stream=window.ASHFALL_ASSET_DELIVERY_107?.status();
  const average=samples.reduce((a,b)=>a+b,0)/samples.length;
  root.textContent="ASHFALL / RENDER DIAGNOSTICS\n"+
   "FPS: "+fps.toFixed(1)+"   30s avg: "+average.toFixed(1)+"\n"+
   "Production assets: "+(stream?.loaded??"n/a")+" cached\n"+
   "Loading: "+(stream?.active??"n/a")+" active / "+(stream?.queued??"n/a")+" queued\n"+
   "Cache hits: "+(stream?.cacheHits??"n/a")+"\n"+
   "Priority promotions: "+(stream?.promotions??"n/a")+"\n"+
   "Failed requests: "+(stream?.failures??"n/a")+"\n"+
   "Oversized images: "+(stream?.oversized??"n/a")+"\n"+
   "Ctrl+Shift+F to close";
 }
 requestAnimationFrame(frame);
}
function toggle(){
 visible=!visible;root.hidden=!visible;
 if(visible){last=performance.now();frameCount=0;requestAnimationFrame(frame)}
}
function init(){
 document.body.append(root);
 document.addEventListener("keydown",event=>{
  if(event.ctrlKey&&event.shiftKey&&event.code==="KeyF"){
   event.preventDefault();toggle();
  }
 });
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init,{once:true});else init();
window.ASHFALL_PERFORMANCE_114=Object.freeze({toggle,isVisible:()=>visible});
})();