/* ASHFALL 96 — settlement environment rebuild.
   World-coordinate, cached illustrated terrain and a navigable road network.
   No gameplay mutation; retains original renderer and its building hitboxes. */
(function(){
"use strict";
const settings={enabled:true,quality:"high",maxTexturePixels:16777216};
let cache=null,cacheKey="",error=null;
const randSeed=seed=>()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296};
const iso=(x,y)=>({x:(x-y)*64,y:(x+y)*32});
const sites=[[-3.5,-3.5],[4.5,-5],[-5.5,3],[5.5,4.5],[-.5,6], [.5,-7]];
function stroke(g,pts,width,color){
 g.beginPath();pts.forEach(([x,y],i)=>i?g.lineTo(x,y):g.moveTo(x,y));g.lineWidth=width;g.strokeStyle=color;g.lineCap="round";g.lineJoin="round";g.stroke();
}
function build(){
 const size=settings.quality==="low"?2048:4096;
 const c=document.createElement("canvas");c.width=c.height=size;
 const g=c.getContext("2d",{alpha:false});if(!g)throw Error("Canvas unavailable");
 const r=randSeed(0xA5F4A96),scale=size/4096;
 g.save();g.translate(size/2,size/2);g.scale(scale,scale);
 const base=g.createLinearGradient(-1900,-1700,1600,1600);
 base.addColorStop(0,"#69764e");base.addColorStop(.45,"#687750");base.addColorStop(1,"#495e43");
 g.fillStyle=base;g.fillRect(-2048,-2048,4096,4096);
 // Broad color masses, natural erosion, reclaimed vegetation.
 for(let i=0;i<700;i++){
  const x=(r()-.5)*4100,y=(r()-.5)*4100,rad=35+r()*230;
  const palette=["111,129,68","139,120,79","51,98,52","184,161,109","54,78,50"];
  const rgb=palette[Math.floor(r()*palette.length)];
  const grad=g.createRadialGradient(x,y,0,x,y,rad);
  grad.addColorStop(0,"rgba("+rgb+","+(0.06+r()*.19)+")");
  grad.addColorStop(1,"rgba("+rgb+",0)");
  g.fillStyle=grad;g.beginPath();g.ellipse(x,y,rad,rad*(.3+r()*.7),r()*6.28,0,6.283);g.fill();
 }
 // Fine grass fibers and dirt specks, baked once rather than on each frame.
 for(let i=0;i<52000;i++){
  const x=(r()-.5)*4096,y=(r()-.5)*4096;
  g.fillStyle=r()>.55?"rgba(220,209,135,.11)":"rgba(23,65,32,.18)";
  g.fillRect(x,y,1+r()*5,.5+r()*2);
 }
 // A deliberate settlement circulation system: no full-screen crossing highways.
 const hub=iso(-1,-1);
 const routes=[
  [iso(-3.5,-3.5),iso(-2,-2),hub,iso(.5,-7)],
  [hub,iso(2,-2),iso(4.5,-5)],
  [hub,iso(1,1),iso(5.5,4.5)],
  [hub,iso(-2,2),iso(-5.5,3)],
  [hub,iso(-1,4),iso(-.5,6)]
 ];
 for(const route of routes){
  const pts=route.map(p=>[p.x,p.y]);
  stroke(g,pts,88,"rgba(34,45,33,.23)");
  stroke(g,pts,67,"#847b66");
  stroke(g,pts,57,"#777466");
  stroke(g,pts,3,"rgba(208,193,153,.20)");
 }
 // Patches of rubble, scrub, rocks, and grass tufts outside construction footprints.
 function nearRoad(x,y){
  for(const route of routes)for(let j=1;j<route.length;j++){
   const a=route[j-1],b=route[j],dx=b.x-a.x,dy=b.y-a.y;
   const t=Math.max(0,Math.min(1,((x-a.x)*dx+(y-a.y)*dy)/(dx*dx+dy*dy||1)));
   if(Math.hypot(x-a.x-t*dx,y-a.y-t*dy)<58)return true;
  }
  return false;
 }
 function nearSite(x,y){return sites.some(([sx,sy])=>{const p=iso(sx,sy);return Math.hypot(x-p.x,y-p.y)<135})}
 for(let i=0;i<2500;i++){
  const x=(r()-.5)*3800,y=(r()-.5)*3800;
  if(nearRoad(x,y)||nearSite(x,y))continue;
  const type=r();
  if(type<.45){
   g.strokeStyle=r()>.5?"#344d32":"#829357";g.lineWidth=1+r()*2;
   g.beginPath();g.moveTo(x,y);g.lineTo(x-2-r()*4,y-4-r()*9);g.moveTo(x,y);g.lineTo(x+2+r()*4,y-3-r()*8);g.stroke();
  }else if(type<.75){
   g.fillStyle=r()>.5?"#9a987c":"#4d5a4b";
   g.beginPath();g.ellipse(x,y,2+r()*9,1+r()*4,r()*6.28,0,6.283);g.fill();
  }else{
   const radius=4+r()*13;
   g.fillStyle="rgba(25,57,31,.22)";g.beginPath();g.ellipse(x+4,y+5,radius*1.8,radius*.65,0,0,6.283);g.fill();
   g.fillStyle=r()>.5?"#426d3c":"#536f40";
   g.beginPath();g.arc(x,y,radius,0,6.283);g.fill();
   g.fillStyle="rgba(155,171,94,.35)";g.beginPath();g.arc(x-radius*.25,y-radius*.3,radius*.58,0,6.283);g.fill();
  }
 }
 // Small settlement boundary remnants and construction material piles.
 for(const [sx,sy] of sites){
  const p=iso(sx,sy);
  for(let i=0;i<12;i++){
   const angle=r()*6.283,dist=105+r()*65,x=p.x+Math.cos(angle)*dist,y=p.y+Math.sin(angle)*dist;
   if(nearRoad(x,y))continue;
   g.fillStyle=r()>.5?"#827d67":"#4a5545";
   g.fillRect(x,y,4+r()*12,2+r()*5);
  }
 }
 g.restore();return c;
}
function draw(ctx){
 if(!settings.enabled)return false;
 const key=settings.quality;
 if(!cache||cacheKey!==key){
  try{cache=build();cacheKey=key;error=null}catch(e){error=e;console.warn("ASHFALL terrain fallback",e);return false}
 }
 ctx.save();ctx.imageSmoothingEnabled=true;ctx.imageSmoothingQuality="high";
 ctx.drawImage(cache,-2048,-2048,4096,4096);ctx.restore();return true;
}
window.ASHFALL_GROUND={draw,settings,rebuild(){cache=null;cacheKey=""},status(){return {ready:!!cache,textureSize:cache?.width||0,quality:settings.quality,error:error?.message||null}}};
})();
