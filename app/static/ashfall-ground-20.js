/* ASHFALL 20 — Painterly settlement ground, deterministic and cached.
   Visual only. Replaces the repeated flat-color tile field and road diamonds.
   Canvas texture generated once per session; no gameplay state touched. */
(function(){
"use strict";
const state={enabled:true,quality:"high",maxTexturePixels:16777216};
let surface=null,surfaceQuality=null,failed=false;
const authoredRoads=new Image();
let authoredRoadsReady=false;
authoredRoads.decoding="async";
authoredRoads.onload=()=>{authoredRoadsReady=true;try{if(typeof window.draw==="function")window.draw()}catch{}};
authoredRoads.onerror=()=>{authoredRoadsReady=false;console.warn("ASHFALL road artwork unavailable; keeping ground fallback")};
authoredRoads.src="/static/ashfall-art/settlement-roads-95.svg?v=1";
function textureSize(){
 const low=state.quality==="low";
 const requested=low?2048:4096;
 return requested*requested>state.maxTexturePixels?2048:requested;
}
function random(seed){let n=seed>>>0;return ()=>{n=(Math.imul(n,1664525)+1013904223)>>>0;return n/4294967296}}
function makeGround(){
 const size=textureSize(),half=size/2,ratio=size/4096;
 const c=document.createElement("canvas");c.width=size;c.height=size;
 const g=c.getContext("2d",{alpha:false});
 if(!g)return null;
 const rand=random(0xA5F4A11);
 const base=g.createLinearGradient(0,0,size,size);
 base.addColorStop(0,"#637052");base.addColorStop(.43,"#526449");base.addColorStop(1,"#43563f");
 g.fillStyle=base;g.fillRect(0,0,size,size);
 // Broad irregular deposits and reclaimed vegetation, with transparent feathering.
 for(let i=0;i<(size===4096?330:175);i++){
  const x=rand()*size,y=rand()*size,r=32+rand()*195;
  const colors=["122,143,81","153,132,87","45,89,55","177,157,106","75,111,68"];
  const rgb=colors[Math.floor(rand()*colors.length)];
  const grad=g.createRadialGradient(x,y,0,x,y,r);
  grad.addColorStop(0,"rgba("+rgb+","+(0.09+rand()*.20).toFixed(3)+")");
  grad.addColorStop(1,"rgba("+rgb+",0)");
  g.fillStyle=grad;g.beginPath();g.ellipse(x,y,r,r*(.4+rand()*.55),rand()*6.28,0,Math.PI*2);g.fill();
 }
 // Fine natural wear. Never rasterize thousands of marks on every redraw.
 for(let i=0;i<(size===4096?28000:12000);i++){
  const x=rand()*size,y=rand()*size,len=.5+rand()*4;
  g.fillStyle=rand()>.45?"rgba(219,202,141,.095)":"rgba(19,51,25,.15)";
  g.fillRect(x,y,len,.6+rand()*1.5);
 }
 // Distinct vegetation clusters and reclaimed ground; baked once into the cached texture.
 for(let i=0;i<(size===4096?1500:650);i++){
  const x=rand()*size,y=rand()*size,r=(1+rand()*5)*ratio;
  g.fillStyle=rand()>.55?"rgba(34,72,34,.24)":"rgba(149,160,83,.17)";
  g.beginPath();g.ellipse(x,y,r*2.4,r,rand()*6.28,0,Math.PI*2);g.fill();
 }
 // Road corridors cross through the settlement origin. Soft shoulders precede paving.
 g.save();g.translate(half,half);g.scale(ratio,ratio);
 for(const angle of [Math.PI/6,Math.PI-Math.PI/6]){
  g.save();g.rotate(angle);
  g.strokeStyle="rgba(35,39,30,.24)";g.lineWidth=102;g.beginPath();g.moveTo(-2000,0);g.lineTo(2000,0);g.stroke();
  g.strokeStyle="#777368";g.lineWidth=70;g.beginPath();g.moveTo(-2000,0);g.lineTo(2000,0);g.stroke();
  g.strokeStyle="rgba(218,208,175,.17)";g.lineWidth=3;g.beginPath();g.moveTo(-2000,-35);g.lineTo(2000,-35);g.moveTo(-2000,35);g.lineTo(2000,35);g.stroke();
  // Distressed, irregular seams in the paving.
  for(let i=0;i<175;i++){
   const x=-1600+rand()*3200,y=(rand()-.5)*80;
   g.strokeStyle=rand()>.5?"rgba(14,26,25,.22)":"rgba(188,165,126,.14)";
   g.lineWidth=.8+rand()*2;
   g.beginPath();g.moveTo(x,y);g.lineTo(x+5+rand()*26,y+(rand()-.5)*10);g.stroke();
  }
  g.restore();
 }
 g.restore();
 return c;
}
function draw(ctx){
 if(!state.enabled)return false;
 if(failed)return false;
 const nextQuality=state.quality+"|"+textureSize();
 if(!surface||surfaceQuality!==nextQuality){
  try{surface=makeGround();surfaceQuality=nextQuality;}catch(error){
   failed=true;console.warn("ASHFALL ground texture unavailable; using tile fallback",error);return false;
  }
 }
 if(!surface)return false;
 // Fixed world footprint regardless of texture resolution.
 ctx.imageSmoothingEnabled=true;ctx.imageSmoothingQuality="high";
 ctx.drawImage(surface,-2048,-2048,4096,4096);
 // Asset-backed road material, mapped to the cached ground world coordinates.
 if(authoredRoadsReady&&authoredRoads.naturalWidth){
  ctx.save();ctx.globalAlpha=.30;
  ctx.drawImage(authoredRoads,-2048,-2048,4096,4096);
  ctx.restore();
 }
 return true;
}
window.ASHFALL_GROUND={draw,settings:state,rebuild:()=>{surface=null;surfaceQuality=null;failed=false},status:()=>({textureSize:surface?.width||0,quality:state.quality,ready:!!surface,failed})};
})();
