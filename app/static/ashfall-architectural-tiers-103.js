/* ASHFALL 103 — 50-stage architectural evolution visual layer.
   Distinct incremental trim, reinforcements, roof hardware and Crystal Era
   ornamentation. Pure canvas art, not a claim of 50 authored 3D models. */
(function(){
"use strict";
const palette=["#d8a875","#b8c2bd","#a5b8a7","#d2a47a","#9bb5c5","#b5a991"];
function hash(s){let h=2166136261;for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619)}return h>>>0}
function draw(ctx,x,y,w,h,key,level){
 if(!Number.isFinite(level)||level<=0)return;
 const n=Math.max(1,Math.min(50,Math.floor(level))),crystal=n>25;
 const eraLevel=crystal?n-25:n;
 const base=hash(key),color=palette[base%palette.length];
 const progression=eraLevel/25;
 const p=(u,v)=>[x+u*w,y+v*h];
 function line(a,b,stroke,lw=1.3){
  ctx.strokeStyle=stroke;ctx.lineWidth=lw;ctx.beginPath();
  ctx.moveTo(...p(...a));ctx.lineTo(...p(...b));ctx.stroke();
 }
 function diamond(u,v,rx,ry,fill,stroke){
  const [cx,cy]=p(u,v);ctx.beginPath();ctx.moveTo(cx,cy-ry);
  ctx.lineTo(cx+rx,cy);ctx.lineTo(cx,cy+ry);ctx.lineTo(cx-rx,cy);ctx.closePath();
  ctx.fillStyle=fill;ctx.fill();if(stroke){ctx.strokeStyle=stroke;ctx.lineWidth=1.2;ctx.stroke()}
 }
 ctx.save();
 // Architecturally aligned to the illustrated isometric plinth.
 const perimeter=[[.15,.71],[.5,.87],[.85,.71],[.5,.55]];
 const accent=crystal?"rgba(167,210,255,.88)":color;
 const dark=crystal?"rgba(43,78,115,.65)":"rgba(47,58,59,.72)";
 // Progressive perimeter bracing: one additional segment every 2 levels.
 const count=Math.min(12,Math.ceil(eraLevel/2));
 for(let i=0;i<count;i++){
  const side=Math.floor(i/3),t=((i%3)+1)/4;
  const a=perimeter[side],b=perimeter[(side+1)%4];
  const u=a[0]+(b[0]-a[0])*t,v=a[1]+(b[1]-a[1])*t;
  const [px,py]=p(u,v);
  ctx.fillStyle=dark;ctx.fillRect(px-2.5,py-5,5,10);
  ctx.fillStyle=accent;ctx.fillRect(px-1,py-4,2,7);
 }
 // Roof upgrades: antennas, solar tiles and reinforced rails.
 if(eraLevel>=5){
  for(let i=0;i<Math.min(5,Math.floor(eraLevel/5));i++){
   const u=.31+i*.095,v=.36+(i%2)*.045;
   diamond(u,v,7+progression*2,3.3,crystal?"#46678a":"#50636b",accent);
  }
 }
 if(eraLevel>=10){
  line([.24,.43],[.5,.30],accent,2);
  line([.5,.30],[.75,.43],accent,2);
  line([.24,.43],[.24,.47],dark,3);
  line([.75,.43],[.75,.47],dark,3);
 }
 if(eraLevel>=15){
  for(let i=0;i<3;i++){
   const u=.37+i*.12,v=.28-(i%2)*.04;
   line([u,v],[u,v-.045],dark,3);
   const [cx,cy]=p(u,v-.045);
   ctx.fillStyle=accent;ctx.beginPath();ctx.arc(cx,cy,2.1,0,Math.PI*2);ctx.fill();
  }
 }
 if(eraLevel>=20){
  diamond(.5,.52,13,5,crystal?"#7bb7d9":"#b99a6b",dark);
  line([.31,.64],[.5,.73],accent,1.6);
  line([.5,.73],[.69,.64],accent,1.6);
 }
 if(crystal){
  // Crystal Era: coherent blue-violet lighting, never random neon shapes.
  const glow=ctx.createRadialGradient(x+w*.5,y+h*.4,1,x+w*.5,y+h*.4,w*.43);
  glow.addColorStop(0,"rgba(111,176,250,"+(.035+progression*.09)+")");
  glow.addColorStop(1,"rgba(111,176,250,0)");
  ctx.fillStyle=glow;ctx.fillRect(x,y,w,h);
  const shards=Math.min(8,Math.ceil(eraLevel/3));
  for(let i=0;i<shards;i++){
   const u=.23+(i%4)*.18,v=.61+Math.floor(i/4)*.10;
   const [cx,cy]=p(u,v),size=3+progression*6;
   ctx.beginPath();ctx.moveTo(cx,cy-size*1.8);ctx.lineTo(cx+size*.45,cy);
   ctx.lineTo(cx,cy+size*.5);ctx.lineTo(cx-size*.45,cy);ctx.closePath();
   ctx.fillStyle="rgba(121,205,255,"+(.35+progression*.45)+")";ctx.fill();
   ctx.strokeStyle="rgba(209,232,255,.7)";ctx.lineWidth=.8;ctx.stroke();
  }
  if(eraLevel>=12){
   ctx.shadowColor="#76c8ff";ctx.shadowBlur=5+progression*12;
   line([.18,.72],[.5,.86],"rgba(116,203,255,.7)",1.7);
   line([.5,.86],[.82,.72],"rgba(116,203,255,.7)",1.7);
   ctx.shadowBlur=0;
  }
 }
 ctx.restore();
}
window.ASHFALL_ARCHITECTURAL_TIERS_103=Object.freeze({draw,levels:50,standard:25,crystal:25});
})();