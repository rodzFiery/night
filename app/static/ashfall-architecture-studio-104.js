/* ASHFALL 104 — Architecture Art Studio.
   Visual-only inspection of every registered building across 50 art stages.
   Never writes game state or modifies progression. */
(function(){
"use strict";
function init(){
 const registry=window.ASHFALL_BUILDINGS_100;
 if(!registry||!window.ASHFALL_ART)return;
 const root=document.createElement("section");
 root.id="af-art-studio";root.hidden=true;root.setAttribute("role","dialog");
 root.setAttribute("aria-label","ASHFALL architecture art studio");
 root.innerHTML='<header><div><small>ASHFALL / VISUAL PRODUCTION</small><h2>ARCHITECTURE STUDIO</h2></div><button type="button" data-close aria-label="Close architecture studio">✕</button></header><div class="af-studio-controls"><label>Building<select id="af-studio-building"></select></label><label>Evolution level <output id="af-studio-value">1</output><input id="af-studio-level" type="range" min="1" max="50" value="1"></label><div id="af-studio-era">STANDARD ERA · LEVEL 01</div></div><div class="af-studio-stage"><canvas id="af-studio-canvas" width="1100" height="720" aria-label="Isometric building evolution preview"></canvas></div><footer>Artwork preview only. Crystal levels are visual concepts; no gameplay upgrades are applied. Missing raster art uses original vector architecture.</footer>';
 const launch=document.createElement("button");launch.type="button";launch.id="af-studio-launch";launch.textContent="◈ Architecture Studio";launch.title="Inspect all buildings and 50 visual evolution levels";
 document.body.append(launch,root);
 const select=root.querySelector("#af-studio-building"),slider=root.querySelector("#af-studio-level"),output=root.querySelector("#af-studio-value"),era=root.querySelector("#af-studio-era"),canvas=root.querySelector("canvas"),ctx=canvas.getContext("2d");
 for(const b of registry.buildings){const option=document.createElement("option");option.value=b.key;option.textContent=b.name+(b.status==="planned"?" · Concept":"");select.append(option)}
 function draw(){
  if(!ctx)return;
  const w=canvas.width,h=canvas.height,level=Number(slider.value),key=select.value;
  const stage=registry.stage(level);
  output.textContent=String(level);
  era.textContent=stage.era==="standard"?"STANDARD ERA · LEVEL "+String(stage.eraLevel).padStart(2,"0"):"CRYSTAL ERA · TIER "+String(stage.eraLevel).padStart(2,"0");
  const grad=ctx.createLinearGradient(0,0,w,h);
  grad.addColorStop(0,stage.era==="crystal"?"#12283b":"#34403c");
  grad.addColorStop(1,stage.era==="crystal"?"#101421":"#1b2222");
  ctx.fillStyle=grad;ctx.fillRect(0,0,w,h);
  // Non-interactive preview pedestal; consistent perspective and scale.
  ctx.save();ctx.translate(w/2,h*.68);
  ctx.fillStyle="#0c181b";ctx.beginPath();ctx.ellipse(0,45,300,95,0,0,Math.PI*2);ctx.fill();
  ctx.fillStyle="#445657";ctx.beginPath();ctx.moveTo(-265,18);ctx.lineTo(0,-112);ctx.lineTo(265,18);ctx.lineTo(0,152);ctx.closePath();ctx.fill();
  ctx.strokeStyle=stage.era==="crystal"?"#81b5f0":"#b39b75";ctx.lineWidth=4;ctx.stroke();
  const b={height:42,width:3,w:3,h:3};
  // The art renderer uses groundY=pos.y+b.height+level*4.
  const pos={x:0,y:-42-level*4-40};
  window.ASHFALL_ART.render(ctx,pos,b,key,level,false);
  ctx.restore();
  ctx.fillStyle="#d5d9d4";ctx.font="700 22px Segoe UI, sans-serif";ctx.textAlign="center";
  ctx.fillText(registry.byKey[key]?.name||key,w/2,55);
  ctx.fillStyle="#a9b7b4";ctx.font="15px Segoe UI, sans-serif";
  ctx.fillText("EVOLUTION "+String(level).padStart(2,"0")+" / 50",w/2,86);
 }
 let raf=0;function queue(){cancelAnimationFrame(raf);raf=requestAnimationFrame(draw)}
 launch.addEventListener("click",()=>{root.hidden=false;queue()});
 root.querySelector("[data-close]").addEventListener("click",()=>{root.hidden=true});
 select.addEventListener("change",queue);slider.addEventListener("input",queue);
 document.addEventListener("keydown",e=>{if(e.key==="Escape")root.hidden=true});
 // Render again when asynchronous SVGs and raster assets finish loading.
 const observer=setInterval(()=>{if(!root.hidden)queue()},900);
 window.addEventListener("pagehide",()=>clearInterval(observer),{once:true});
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init,{once:true});else init();
})();