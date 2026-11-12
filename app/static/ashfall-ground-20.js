/* ASHFALL 20 — Painterly settlement ground, deterministic and cached.
   Visual only. Replaces the repeated flat-color tile field and road diamonds.
   Canvas texture generated once per session; no gameplay state touched. */
(function(){
"use strict";
const state={enabled:true,quality:"high"};
let surface=null;
function random(seed){let n=seed>>>0;return ()=>{n=(Math.imul(n,1664525)+1013904223)>>>0;return n/4294967296}}
function makeGround(){
 const size=3072,half=size/2;
 const c=document.createElement("canvas");c.width=size;c.height=size;
 const g=c.getContext("2d",{alpha:false});
 if(!g)return null;
 const rand=random(0xA5F4A11);
 const base=g.createLinearGradient(0,0,size,size);
 base.addColorStop(0,"#3b4740");base.addColorStop(.43,"#343e37");base.addColorStop(1,"#263630");
 g.fillStyle=base;g.fillRect(0,0,size,size);
 // Broad irregular deposits and reclaimed vegetation, with transparent feathering.
 for(let i=0;i<330;i++){
  const x=rand()*size,y=rand()*size,r=32+rand()*195;
  const colors=["91,103,79","91,79,65","34,66,54","105,91,70","55,76,63"];
  const rgb=colors[Math.floor(rand()*colors.length)];
  const grad=g.createRadialGradient(x,y,0,x,y,r);
  grad.addColorStop(0,"rgba("+rgb+","+(0.055+rand()*.14).toFixed(3)+")");
  grad.addColorStop(1,"rgba("+rgb+",0)");
  g.fillStyle=grad;g.beginPath();g.ellipse(x,y,r,r*(.4+rand()*.55),rand()*6.28,0,Math.PI*2);g.fill();
 }
 // Fine natural wear. Never rasterize thousands of marks on every redraw.
 for(let i=0;i<17000;i++){
  const x=rand()*size,y=rand()*size,len=.5+rand()*4;
  g.fillStyle=rand()>.45?"rgba(202,185,145,.065)":"rgba(8,21,21,.13)";
  g.fillRect(x,y,len,.6+rand()*1.5);
 }
 // Road corridors cross through the settlement origin. Soft shoulders precede paving.
 g.save();g.translate(half,half);
 for(const angle of [Math.PI/6,Math.PI-Math.PI/6]){
  g.save();g.rotate(angle);
  g.strokeStyle="rgba(14,22,23,.35)";g.lineWidth=118;g.beginPath();g.moveTo(-2000,0);g.lineTo(2000,0);g.stroke();
  g.strokeStyle="#55574c";g.lineWidth=88;g.beginPath();g.moveTo(-2000,0);g.lineTo(2000,0);g.stroke();
  g.strokeStyle="rgba(159,140,109,.24)";g.lineWidth=3;g.beginPath();g.moveTo(-2000,-35);g.lineTo(2000,-35);g.moveTo(-2000,35);g.lineTo(2000,35);g.stroke();
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
 if(!surface)surface=makeGround();
 if(!surface)return false;
 // Existing world geometry extends about 1700px from the origin.
 ctx.drawImage(surface,-1536,-1536);
 return true;
}
window.ASHFALL_GROUND={draw,settings:state,rebuild:()=>{surface=null}};
})();
