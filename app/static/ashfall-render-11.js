/* ASHFALL 11 — Architectural Rendering Atelier
   Layered Canvas detailing, deterministic terrain, building-specific silhouettes.
   No gameplay mutations. Uses world canvas transform and existing hit targets. */
(function(){
"use strict";
const A={enabled:true,detail:"high",textures:new Map(),tick:0};
function seed(x,y){let v=Math.sin(x*127.1+y*311.7)*43758.5453;return v-Math.floor(v)}
function path(ctx,pts,color,stroke){ctx.beginPath();pts.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));ctx.closePath();ctx.fillStyle=color;ctx.fill();if(stroke){ctx.strokeStyle=stroke;ctx.lineWidth=1;ctx.stroke()}}
function diamond(ctx,iso,x,y,fill,stroke){const a=iso(x,y),b=iso(x+1,y),c=iso(x+1,y+1),d=iso(x,y+1);path(ctx,[a,b,c,d],fill,stroke)}
function line(ctx,x1,y1,x2,y2,color,width=1){ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.strokeStyle=color;ctx.lineWidth=width;ctx.stroke()}
function shadow(ctx,x,y,rx,ry,opacity=.2){ctx.save();ctx.fillStyle="rgba(0,0,0,"+opacity+")";ctx.beginPath();ctx.ellipse(x,y,rx,ry,0,0,Math.PI*2);ctx.fill();ctx.restore()}
function prism(ctx,x,y,w,h,color,light){path(ctx,[{x:x-w,y},{x,y:h+y*.0},{x:x+w,y},{x,y:h+y*.0}],color);line(ctx,x,y-h,x,y,light,2)}
function terrain(ctx,iso,x,y,kind,variation,settlement=false){
 if(!A.enabled)return;
 const n=seed(x+53,y+91),p=iso(x+.5,y+.5);
 ctx.save();
 // Soil and road wear use the existing isometric tile, not a separate overlay.
 if(n>.29){
  const tone=settlement?"#d6bd8b":kind==="forest"?"#85a47a":kind==="ridge"?"#b6a99a":kind==="dust"?"#e0b98a":"#9aab8b";
  ctx.strokeStyle=tone;ctx.globalAlpha=.13+.12*variation;ctx.lineWidth=1;
  for(let i=0;i<3;i++){const a=seed(x+i*3,y+2)*40-20,b=seed(x+7,y+i*5)*12-6;line(ctx,p.x+a-9,p.y+b,p.x+a+7,p.y+b-2,tone,1)}
 }
 if(!settlement&&kind==="ridge"&&n>.65){
  path(ctx,[{x:p.x-15,y:p.y+2},{x:p.x-5,y:p.y-15},{x:p.x+3,y:p.y-5},{x:p.x+13,y:p.y+3}],"#7f8983");
  path(ctx,[{x:p.x-5,y:p.y-15},{x:p.x+3,y:p.y-5},{x:p.x+13,y:p.y+3},{x:p.x+1,y:p.y-2}],"#4e6262");
 }
 if(!settlement&&kind==="forest"&&n>.74){
  for(let i=0;i<2;i++){const xx=p.x+i*10-6,yy=p.y+i*2;
   line(ctx,xx,yy,xx,yy-13,"#493f35",2);
   path(ctx,[{x:xx-8,y:yy-7},{x:xx,y:yy-27},{x:xx+8,y:yy-7}],"#284b3e","#456f55");
   path(ctx,[{x:xx-6,y:yy-14},{x:xx,y:yy-32},{x:xx+6,y:yy-14}],"#54725a");
  }
 }
 if(settlement&&n>.85){
  ctx.fillStyle="#796e57";ctx.fillRect(p.x-5,p.y-3,9,5);
  line(ctx,p.x-4,p.y-2,p.x+4,p.y+1,"#b8a37b");
 }
 ctx.restore()
}
function detail(ctx,iso,b,key,level,constructing){
 if(!A.enabled)return;
 const x=b.x,y=b.y,w=b.w,h=b.h,height=b.height+level*4;
 const p=iso(x+w/2,y+h/2),roof=p.y-height,crystal=level>30,stage=Math.max(0,level-30);
 ctx.save();
 shadow(ctx,p.x,p.y+8,w*54,h*23,.3);
 // Architectural footprint, anchor bolts, hazard striping.
 const corners=[iso(x-.12,y-.12),iso(x+w+.12,y-.12),iso(x+w+.12,y+h+.12),iso(x-.12,y+h+.12)];
 ctx.strokeStyle=crystal?"#a78bef":"#a8916b";ctx.lineWidth=2;
 ctx.beginPath();corners.forEach((v,i)=>i?ctx.lineTo(v.x,v.y):ctx.moveTo(v.x,v.y));ctx.closePath();ctx.stroke();
 for(let i=0;i<4;i++){const v=corners[i];ctx.fillStyle=crystal?"#b6a4ff":"#d2ae76";ctx.fillRect(v.x-3,v.y-3,6,6)}
 // Tall structural seams, ventilation and lit windows.
 for(const side of [-1,1]){
  const sx=p.x+side*(w*22);
  line(ctx,sx,p.y-8,sx,p.y-height*.77,"#101c25",5);
  line(ctx,sx+side*2,p.y-12,sx+side*2,p.y-height*.73,crystal?"#9e87df":"#667b7c",1.5);
 }
 for(let i=0;i<Math.min(8,2+Math.floor(level/5));i++){
  const offset=(i-(Math.min(8,2+Math.floor(level/5))-1)/2)*13;
  ctx.fillStyle=crystal?"#b8a3ff":"#e7b778";ctx.fillRect(p.x+offset-3,p.y-height*.56,6,4);
  ctx.fillStyle="#08131b";ctx.fillRect(p.x+offset-2,p.y-height*.56+1,2,2)
 }
 // Unique facility geometry, drawn above the shared foundation.
 if(key==="hq"){
  for(const side of [-1,1]){
   const sx=p.x+side*39;
   ctx.fillStyle="#455660";ctx.fillRect(sx-9,roof-25,18,27);
   ctx.fillStyle="#b79a72";ctx.fillRect(sx-11,roof-27,22,5);
   line(ctx,sx,roof-25,sx,roof-49,crystal?"#ae9dff":"#b0b9b3",2);
  }
  const beacon=ctx.createRadialGradient(p.x,roof-70,1,p.x,roof-70,26);
  beacon.addColorStop(0,crystal?"#bca3ffad":"#ffc780aa");beacon.addColorStop(1,"#00000000");
  ctx.fillStyle=beacon;ctx.beginPath();ctx.arc(p.x,roof-70,26,0,Math.PI*2);ctx.fill();
 }else if(key==="farm"){
  for(let i=0;i<5;i++){
   const q=iso(x+.25+i*.46,y+h-.4);
   line(ctx,q.x-10,q.y-3,q.x+18,q.y+8,"#7e9b58",5);
   line(ctx,q.x-10,q.y-7,q.x+18,q.y+4,"#b1c878",2)
  }
 }else if(key==="lumber"){
  for(let i=0;i<4;i++){const q=iso(x+.4+i*.5,y+h-.25);
   ctx.fillStyle="#9e7654";ctx.fillRect(q.x-16,q.y-15,34,8);
   ctx.fillStyle="#d1ae7a";ctx.beginPath();ctx.arc(q.x+18,q.y-11,4,0,Math.PI*2);ctx.fill()}
 }else if(key==="salvage"){
  for(let i=0;i<3;i++){const q=iso(x+.5+i*.7,y+.5);
   ctx.fillStyle="#899a99";ctx.fillRect(q.x-9,q.y-31,18,25);
   ctx.fillStyle="#c2b9a4";ctx.fillRect(q.x-11,q.y-32,22,4)}
  line(ctx,p.x+38,roof+6,p.x+38,roof-52,"#d3a46f",4);
  line(ctx,p.x-2,roof-48,p.x+73,roof-48,"#d3a46f",3);
  line(ctx,p.x+67,roof-48,p.x+67,roof-13,"#778b8e",1)
 }else if(key==="fuel"){
  for(let i=0;i<3;i++){const q=iso(x+.5+i*.68,y+.6);
   ctx.fillStyle="#627779";ctx.fillRect(q.x-11,q.y-35,22,31);
   ctx.fillStyle="#a9b8af";ctx.beginPath();ctx.ellipse(q.x,q.y-35,11,5,0,0,Math.PI*2);ctx.fill();
   line(ctx,q.x-10,q.y-20,q.x+10,q.y-20,"#caa16a",3)}
 }else if(key==="barracks"){
  for(const side of [-1,1]){const q=iso(x+w/2+side*.7,y+h/2);
   ctx.fillStyle="#36474c";ctx.fillRect(q.x-14,roof-13,28,16);
   ctx.fillStyle="#a48d71";ctx.fillRect(q.x-15,roof-14,30,4)}
  ctx.strokeStyle="#d7a979";ctx.lineWidth=3;ctx.strokeRect(p.x-12,p.y-height*.6,24,18)
 }
 // Crystal architecture has 25 visual growth steps, not just a hue change.
 if(crystal){
  const count=Math.min(10,3+Math.floor(stage/3));
  for(let i=0;i<count;i++){
   const spread=(i-(count-1)/2)*16,hh=12+stage*.8+(i%3)*9;
   const bx=p.x+spread,by=roof-3+(i%2)*7;
   path(ctx,[{x:bx-7,y:by},{x:bx,y:by-hh},{x:bx+7,y:by},{x:bx,y:by+5}],i%2?"#6b80c6":"#9375cf","#d5c6ff");
   line(ctx,bx,by-hh,bx,by+4,"#c6d9ff",1)
  }
  ctx.strokeStyle="#ae91ff";ctx.lineWidth=1.5+stage/10;
  ctx.beginPath();ctx.ellipse(p.x,roof+4,26+stage*.7,10+stage*.15,0,0,Math.PI*2);ctx.stroke()
 }
 if(constructing){
  ctx.strokeStyle="#e7ae6d";ctx.lineWidth=2;
  for(let i=-1;i<=1;i++){const xx=p.x+i*30;line(ctx,xx,p.y-8,xx,roof-24,"#b78d56",2);for(let j=0;j<3;j++)line(ctx,xx-9,roof+j*18,xx+9,roof+j*18,"#e7ae6d",2)}
 }
 ctx.restore()
}
window.ASHFALL_RENDER_ATELIER={terrain,detail,settings:A};
})();
