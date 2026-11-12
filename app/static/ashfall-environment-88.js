/* ASHFALL 88 — Environmental Renaissance
   Deterministic cached settlement dressing. World-space only; never changes
   terrain collision, building positions, gameplay, or hit targets.
*/
(function(){
"use strict";
const settings={enabled:true,quality:"high",vegetation:true,ruins:true,roads:true};
let cache=null,cacheKey="",failed=false;
const SIZE=3072,HALF=SIZE/2;
function rng(seed){let n=seed>>>0;return()=>{n=(Math.imul(n,1664525)+1013904223)>>>0;return n/4294967296}}
function stroke(g,points,color,width=1){
 g.beginPath();points.forEach((p,i)=>i?g.lineTo(p[0],p[1]):g.moveTo(p[0],p[1]));
 g.strokeStyle=color;g.lineWidth=width;g.stroke();
}
function polygon(g,points,color,edge){
 g.beginPath();points.forEach((p,i)=>i?g.lineTo(p[0],p[1]):g.moveTo(p[0],p[1]));
 g.closePath();g.fillStyle=color;g.fill();
 if(edge){g.strokeStyle=edge;g.lineWidth=1;g.stroke()}
}
function paintRoad(g,r){
 // Scarred service tracks and old industrial traffic markings.
 for(const angle of [Math.PI/6,Math.PI-Math.PI/6]){
  g.save();g.rotate(angle);
  for(let i=0;i<90;i++){
   const x=-1380+r()*2760,y=(r()-.5)*78;
   stroke(g,[[x,y],[x+8+r()*32,y+(r()-.5)*6]],r()>.5?"rgba(10,20,18,.29)":"rgba(204,181,134,.18)",.8+r()*2);
  }
  g.setLineDash([25,30]);
  stroke(g,[[-1400,0],[1400,0]],"rgba(209,171,103,.13)",1.8);
  g.setLineDash([]);
  for(let i=0;i<22;i++){
   const x=-1250+i*114;
   stroke(g,[[x,-47],[x+7,-39]],"rgba(244,206,140,.18)",2);
   stroke(g,[[x,47],[x+7,39]],"rgba(244,206,140,.18)",2);
  }
  g.restore();
 }
}
function rubble(g,x,y,r){
 g.save();g.translate(x,y);
 g.fillStyle="rgba(7,17,16,.23)";
 g.beginPath();g.ellipse(0,4,r*1.6,r*.5,0,0,Math.PI*2);g.fill();
 for(let i=0;i<7;i++){
  const dx=(r()-0.5)*48,dy=(r()-.5)*20,s=3+r()*10;
  polygon(g,[[dx-s,dy+2],[dx-s*.2,dy-s*.6],[dx+s,dy-s*.1],[dx+s*.6,dy+s*.4]],
    ["#62685c","#797a69","#4a554d","#8d806a"][Math.floor(r()*4)],"rgba(15,27,23,.34)");
 }
 g.restore();
}
function shrub(g,x,y,r){
 const size=4+r()*11;
 g.fillStyle="rgba(6,22,16,.23)";g.beginPath();g.ellipse(x,y+3,size*1.4,size*.42,0,0,Math.PI*2);g.fill();
 for(let j=0;j<4;j++){
  const dx=(r()-.5)*size,dy=(r()-.5)*size*.35;
  stroke(g,[[x+dx,y+dy+3],[x+dx+(r()-.5)*5,y+dy-size*(.5+r()*.8)]],
    ["#637657","#788263","#9b956c","#4c6753"][Math.floor(r()*4)],1+r()*1.3);
 }
}
function brokenWall(g,x,y,r){
 const length=35+r()*64,height=9+r()*19;
 g.save();g.translate(x,y);g.rotate((r()-.5)*.55);
 polygon(g,[[0,0],[length,0],[length-5,-height],[6,-height]],"#62665d","#323f3b");
 polygon(g,[[0,0],[length,0],[length,6],[0,6]],"#414a43");
 for(let i=0;i<5;i++){
  const px=6+i*(length-12)/5;
  stroke(g,[[px,-height+2],[px+(r()-.5)*5,-2]],"rgba(18,28,26,.4)",1.2);
 }
 g.restore();
}
function create(){
 const c=document.createElement("canvas");c.width=SIZE;c.height=SIZE;
 const g=c.getContext("2d");if(!g)return null;
 const r=rng(0xA5F488);
 g.translate(HALF,HALF);
 if(settings.roads)paintRoad(g,r);
 // Dense edge vegetation; preserve central service corridors and structures.
 const count=settings.quality==="low"?250:620;
 for(let i=0;i<count;i++){
  const x=(r()-.5)*2700,y=(r()-.5)*2700;
  const d=Math.hypot(x,y);
  if(d<310||d>1460)continue;
  if(Math.abs(y-x*.577)<75||Math.abs(y+x*.577)<75)continue;
  if(settings.vegetation&&r()<.68)shrub(g,x,y,r);
  else if(settings.ruins)rubble(g,x,y,r);
 }
 if(settings.ruins){
  // Broken perimeter walls and salvage clusters beyond the six build plots.
  for(let i=0;i<42;i++){
   const angle=r()*Math.PI*2,d=650+r()*670;
   const x=Math.cos(angle)*d,y=Math.sin(angle)*d*.78;
   if(Math.abs(y-x*.577)<100||Math.abs(y+x*.577)<100)continue;
   if(r()<.45)brokenWall(g,x,y,r);else rubble(g,x,y,r);
  }
 }
 return c;
}
function draw(ctx){
 if(!settings.enabled||failed)return;
 const key=JSON.stringify(settings);
 if(!cache||key!==cacheKey){
  try{cache=create();cacheKey=key}catch(e){failed=true;console.warn("ASHFALL environment detail fallback",e)}
 }
 if(!cache)return;
 ctx.save();ctx.imageSmoothingEnabled=true;ctx.imageSmoothingQuality="high";
 ctx.drawImage(cache,-HALF,-HALF,SIZE,SIZE);ctx.restore();
}
window.ASHFALL_ENVIRONMENT_88={draw,settings,rebuild:()=>{cache=null;failed=false},status:()=>({ready:!!cache,failed,quality:settings.quality})};
})();
