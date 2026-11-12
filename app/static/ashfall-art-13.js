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
 img.src="/static/ashfall-art/"+key+".svg?v="+(key==="hq"?3:2);
 sprites.set(key,img);
}

// ASHFALL 14 — deterministic architectural atmosphere, anchored to each sprite.
// Purely visual: no gameplay, economy, hitboxes, or world coordinates are changed.
function atmosphere(ctx,pos,key,level,constructing,width,height){
 const x=pos.x,y=pos.y;
 const seed=key.split("").reduce((a,ch)=>a*31+ch.charCodeAt(0),17);
 const upgraded=level>=10,elite=level>=30;
 ctx.save();
 // Ground contact shadow and subtle warm ambient bounce.
 const shade=ctx.createRadialGradient(x,y+12,8,x,y+12,width*.48);
 shade.addColorStop(0,"rgba(0,0,0,.42)");
 shade.addColorStop(.58,"rgba(0,0,0,.22)");
 shade.addColorStop(1,"rgba(0,0,0,0)");
 ctx.fillStyle=shade;ctx.beginPath();ctx.ellipse(x,y+12,width*.48,height*.19,0,0,Math.PI*2);ctx.fill();
 if(level>0){
  const glow=ctx.createRadialGradient(x,y-height*.39,1,x,y-height*.39,width*.31);
  glow.addColorStop(0,elite?"rgba(164,130,255,.17)":upgraded?"rgba(255,188,111,.12)":"rgba(255,180,98,.07)");
  glow.addColorStop(1,"rgba(255,180,98,0)");
  ctx.fillStyle=glow;ctx.beginPath();ctx.ellipse(x,y-height*.39,width*.31,height*.35,0,0,Math.PI*2);ctx.fill();
 }
 // Stable architectural floor markers: never flicker between frames.
 ctx.lineWidth=1.2;ctx.strokeStyle=elite?"rgba(179,155,255,.55)":"rgba(225,176,111,.36)";
 for(let i=0;i<4;i++){
  const a=(i*Math.PI/2)+Math.PI/4;
  const px=x+Math.cos(a)*width*.36,py=y+Math.sin(a)*height*.13;
  ctx.beginPath();ctx.moveTo(px-4,py);ctx.lineTo(px+4,py);ctx.stroke();
 }
 // Construction beacon is intentionally restrained to preserve readability.
 if(constructing){
  const by=y-height*.81;
  ctx.fillStyle="rgba(255,184,91,.85)";
  ctx.beginPath();ctx.arc(x+width*.23,by,3.5,0,Math.PI*2);ctx.fill();
 }
 // Individualized atmospheric motes around each facility.
 for(let i=0;i<5;i++){
  const n=(seed+i*73)%97/97;
  const dx=(n-.5)*width*.66;
  const dy=height*(.12+((seed+i*19)%71)/71*.34);
  ctx.fillStyle=elite?"rgba(189,168,255,.35)":"rgba(237,198,142,.25)";
  ctx.fillRect(x+dx,y-dy,1.3,1.3);
 }
 ctx.restore();
}

function render(ctx,pos,b,key,level,constructing){
 if(!config.enabled)return false;
 const img=sprites.get(key);
 if(!img||!img.complete||!img.naturalWidth)return false;
 const size=Math.min(1.15,Math.max(.77,.83+Math.min(level,55)*.005))*config.scale;
 const width=340*size,height=266*size;
 // Existing building position is the center of its roof.
 // Offset sprite downward to align the illustrated plinth with the footprint.
 const groundY=pos.y+b.height+level*4;
 const left=pos.x-width/2,top=groundY-height*.93;
 ctx.save();
 if(config.glow&&level>30){
  const strength=Math.min(28,8+(level-30)*.7);
  ctx.shadowColor="#a98aff";ctx.shadowBlur=strength;
 }
 atmosphere(ctx,{x:pos.x,y:groundY},key,level,constructing,width,height);
 ctx.imageSmoothingEnabled=true;
 ctx.imageSmoothingQuality="high";
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