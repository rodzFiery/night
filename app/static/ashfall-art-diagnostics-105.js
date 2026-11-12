/* ASHFALL 105 — production art diagnostics.
   Inspect one requested raster asset at a time, cache outcomes, and explain
   vector fallback without pretending placeholder art is production-ready. */
(function(){
"use strict";
const cache=new Map();
const pending=new Map();
function check(key,level){
 const registry=window.ASHFALL_BUILDINGS_100;
 if(!registry||!registry.byKey[key])return Promise.resolve({status:"invalid"});
 const url=registry.filename(key,level);
 const manifest=window.ASHFALL_ART_MANIFEST_116;
 if(Array.isArray(manifest)&&!manifest.includes(url.slice(url.lastIndexOf("/")+1)))return Promise.resolve({status:"unpublished",url});
 if(cache.has(url))return Promise.resolve(cache.get(url));
 if(pending.has(url))return pending.get(url);
 const promise=new Promise(resolve=>{
  const img=new Image();img.decoding="async";
  img.onload=()=>{
   const result={status:"ready",url,width:img.naturalWidth,height:img.naturalHeight};
   cache.set(url,result);pending.delete(url);resolve(result);
  };
  img.onerror=()=>{
   const result={status:"fallback",url};
   cache.set(url,result);pending.delete(url);resolve(result);
  };
  img.src=url;
 });
 pending.set(url,promise);return promise;
}
function init(){
 const studio=document.getElementById("af-art-studio");
 if(!studio)return;
 const controls=studio.querySelector(".af-studio-controls");
 const diagnostic=document.createElement("div");
 diagnostic.id="af-studio-diagnostics";
 diagnostic.setAttribute("aria-live","polite");
 diagnostic.innerHTML='<span class="af-diag-led"></span><span class="af-diag-status">Checking artwork…</span><small class="af-diag-path"></small>';
 controls.append(diagnostic);
 const building=studio.querySelector("#af-studio-building"),level=studio.querySelector("#af-studio-level");
 let generation=0;
 async function update(){
  const current=++generation,key=building.value,n=Number(level.value);
  diagnostic.dataset.state="loading";
  diagnostic.querySelector(".af-diag-status").textContent="Checking authored raster art…";
  diagnostic.querySelector(".af-diag-path").textContent="";
  const result=await check(key,n);
  if(current!==generation)return;
  diagnostic.dataset.state=result.status;
  if(result.status==="ready"){
   diagnostic.querySelector(".af-diag-status").textContent="Production WebP available · "+result.width+" × "+result.height;
  }else if(result.status==="unpublished"){
   diagnostic.querySelector(".af-diag-status").textContent="Production art not published · illustrated fallback active";
  }else{
   diagnostic.querySelector(".af-diag-status").textContent="Authored WebP unavailable · displaying illustrated fallback";
  }
  diagnostic.querySelector(".af-diag-path").textContent=result.url||"";
 }
 building.addEventListener("change",update);
 level.addEventListener("input",update);
 document.getElementById("af-studio-launch")?.addEventListener("click",update);
 // Lightweight two-stage comparison. One reference image is rendered using
 // the existing art engine and remains purely a preview.
 const comparison=document.createElement("div");
 comparison.id="af-studio-compare";
 comparison.innerHTML='<label><input type="checkbox" id="af-studio-compare-toggle"> Compare with level 1</label><span id="af-studio-compare-caption"></span>';
 controls.append(comparison);
 const toggle=comparison.querySelector("input"),canvas=studio.querySelector("#af-studio-canvas");
 const original=window.ASHFALL_ART.render;
 // Draw comparison into an overlay canvas, without monkey-patching the renderer.
 const overlay=document.createElement("canvas");
 overlay.id="af-studio-compare-canvas";overlay.width=1100;overlay.height=720;overlay.hidden=true;
 canvas.parentNode.append(overlay);
 function renderComparison(){
  if(!toggle.checked||studio.hidden)return;
  const ctx=overlay.getContext("2d");if(!ctx)return;
  const w=overlay.width,h=overlay.height;
  ctx.clearRect(0,0,w,h);
  ctx.fillStyle="rgba(7,15,18,.96)";ctx.fillRect(0,0,w*.5,h);
  ctx.fillStyle="#34403c";ctx.beginPath();ctx.moveTo(50,h*.7);ctx.lineTo(w*.25,h*.46);ctx.lineTo(w*.5-50,h*.7);ctx.lineTo(w*.25,h*.93);ctx.closePath();ctx.fill();
  ctx.save();ctx.translate(w*.25,h*.67);
  original(ctx,{x:0,y:-86},{height:42},building.value,1,false);
  ctx.restore();
  ctx.fillStyle="#e9dfcb";ctx.font="bold 20px Segoe UI";ctx.textAlign="center";
  ctx.fillText("LEVEL 01 · REFERENCE",w*.25,50);
  ctx.fillStyle="rgba(228,235,235,.4)";ctx.fillRect(w*.5-1,0,2,h);
 }
 function sync(){
  const enabled=toggle.checked;
  overlay.hidden=!enabled;
  canvas.classList.toggle("af-studio-half",enabled);
  comparison.querySelector("span").textContent=enabled?"Left: level 1 · Right: selected level":"";
  if(enabled)renderComparison();
 }
 toggle.addEventListener("change",sync);
 building.addEventListener("change",renderComparison);
 level.addEventListener("input",renderComparison);
 document.getElementById("af-studio-launch")?.addEventListener("click",()=>{if(toggle.checked)renderComparison()});
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init,{once:true});else init();
})();