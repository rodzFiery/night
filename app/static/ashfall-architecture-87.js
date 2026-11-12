/* ASHFALL 87 — Architectural Renaissance
   Six hand-authored Canvas detail passes. Uses existing art sprites, camera,
   level gates and building hitboxes. Purely visual; no simulation writes.
*/
(function(){
"use strict";
const evolution=window.ASHFALL_ART_EVOLUTION;
if(!evolution||typeof evolution.draw!=="function")return;
const original=evolution.draw;
const settings={enabled:true,details:true,lighting:true};
const palette={
 hq:["#b2c1bc","#f3b67a","#2c4044"],
 farm:["#a2bd99","#d6d995","#365449"],
 lumber:["#c7a680","#f0bc7e","#55463b"],
 salvage:["#9cbabc","#8cdddc","#354d51"],
 fuel:["#b5bba6","#ffc17b","#48524b"],
 barracks:["#c6aaa0","#f3a38a","#504342"]
};
function stroke(c,pts,color,w=2){
 c.beginPath();pts.forEach((p,i)=>i?c.lineTo(p[0],p[1]):c.moveTo(p[0],p[1]));
 c.strokeStyle=color;c.lineWidth=w;c.stroke();
}
function polygon(c,pts,fill,edge){
 c.beginPath();pts.forEach((p,i)=>i?c.lineTo(p[0],p[1]):c.moveTo(p[0],p[1]));c.closePath();
 c.fillStyle=fill;c.fill();if(edge){c.strokeStyle=edge;c.lineWidth=1;c.stroke()}
}
function rivets(c,x,y,count,dx,dy){
 c.fillStyle="rgba(242,228,200,.55)";
 for(let i=0;i<count;i++){c.beginPath();c.arc(x+i*dx,y+i*dy,1.4,0,Math.PI*2);c.fill()}
}
function hatch(c,x,y,w,h,metal,dark){
 polygon(c,[[x,y],[x+w,y-5],[x+w,y+h-5],[x,y+h]],dark,metal);
 stroke(c,[[x+4,y+5],[x+w-4,y+1]],metal,1);
 stroke(c,[[x+4,y+h-5],[x+w-4,y+h-9]],metal,1);
 rivets(c,x+5,y+6,4,(w-10)/3,-1);
}
function lamp(c,x,y,color,active){
 c.fillStyle="#172b2a";c.fillRect(x-5,y-5,10,10);
 if(active){c.save();c.shadowColor=color;c.shadowBlur=13;c.fillStyle=color;c.fillRect(x-2,y-2,4,4);c.restore()}
 else{c.fillStyle="#866a4d";c.fillRect(x-2,y-2,4,4)}
}
function steel(c,x,y,w,h,metal){
 c.fillStyle=metal;c.fillRect(x,y,w,h);
 c.fillStyle="rgba(14,27,29,.48)";c.fillRect(x+3,y+3,w-6,h-6);
 for(let i=0;i<3;i++)stroke(c,[[x+4,y+5+i*(h-10)/2],[x+w-4,y+5+i*(h-10)/2]],metal,1);
}
function architecture(c,key,level){
 const [metal,accent,dark]=palette[key];
 const advanced=level>=15,crystal=level>=30,legend=level>=50;
 c.save();c.lineJoin="round";c.lineCap="round";
 // Grounded material work: plinth bolts, oxidized service panels and bracing.
 for(let i=0;i<4;i++){
  const x=74+i*49;
  stroke(c,[[x,187],[x+12,192],[x+24,187]],"rgba(8,22,22,.75)",4);
  rivets(c,x+3,189,3,9,0);
 }
 hatch(c,100,151,38,19,metal,dark);
 hatch(c,203,148,35,17,metal,dark);
 stroke(c,[[89,163],[111,172],[133,162]],metal,3);
 stroke(c,[[207,167],[231,178],[248,168]],metal,3);
 if(key==="hq"){
  // Command bunker: shielded observation slit, uplink cabling and fortified crown.
  steel(c,136,119,68,25,metal);
  for(let i=0;i<5;i++)lamp(c,144+i*13,131,accent,level>=5);
  stroke(c,[[154,117],[154,101],[180,88],[206,104],[206,119]],metal,4);
  hatch(c,159,91,42,13,metal,dark);
  if(advanced){
   stroke(c,[[113,122],[113,65],[131,50]],metal,5);
   stroke(c,[[228,119],[228,61],[213,44]],metal,5);
   lamp(c,130,48,accent,true);lamp(c,214,43,accent,true);
  }
 }else if(key==="farm"){
  // Irrigation manifolds, translucent canopy ribs and seedling trays.
  for(let i=0;i<4;i++){
   const x=91+i*39;
   polygon(c,[[x,135],[x+12,126],[x+28,134],[x+16,143]],"#42614d","#9cb48a");
   stroke(c,[[x+5,135],[x+16,128],[x+23,135]],"#bdd9ad",1.5);
  }
  stroke(c,[[87,150],[247,150]],metal,5);
  for(let i=0;i<7;i++)stroke(c,[[96+i*22,150],[96+i*22,165]],accent,1.5);
  if(advanced)for(let i=0;i<3;i++){
   const x=105+i*50;
   stroke(c,[[x,111],[x+20,80],[x+40,111]],metal,3);
   stroke(c,[[x+7,106],[x+20,89],[x+33,106]],"#c4e0bf",2);
  }
 }else if(key==="lumber"){
  // Stacked timber, sawtooth roofing, heavy crane rigging.
  for(let j=0;j<3;j++)for(let i=0;i<5;i++){
   const x=96+i*23+j*5,y=162-j*10;
   c.fillStyle=j%2?"#896a4d":"#ae895d";c.fillRect(x,y,20,7);
   stroke(c,[[x+3,y+2],[x+18,y+2]],"#d9ad78",1);
  }
  stroke(c,[[100,127],[126,101],[145,119],[169,96],[191,117],[216,99],[238,118]],metal,4);
  if(advanced){
   stroke(c,[[236,123],[236,50],[169,50]],metal,5);
   stroke(c,[[185,52],[185,99]],dark,2);
   polygon(c,[[170,99],[201,99],[195,110],[177,110]],accent);
  }
 }else if(key==="salvage"){
  // Sorting bays, hydraulic press, magnetic rail.
  for(let i=0;i<3;i++){
   const x=106+i*42;
   steel(c,x,132,32,26,metal);
   stroke(c,[[x+3,154],[x+28,137]],accent,2);
  }
  stroke(c,[[89,114],[246,114]],metal,6);
  for(let i=0;i<6;i++)rivets(c,94+i*28,114,2,5,0);
  if(advanced){
   steel(c,152,73,42,32,metal);
   stroke(c,[[173,76],[173,49],[212,49]],metal,5);
   lamp(c,213,49,accent,true);
  }
 }else if(key==="fuel"){
  // Storage drums, industrial pipework and safety markings.
  for(let i=0;i<3;i++){
   const x=104+i*51;
   c.fillStyle=metal;c.fillRect(x,114,37,48);
   c.fillStyle=dark;c.beginPath();c.ellipse(x+18.5,114,18.5,7,0,0,Math.PI*2);c.fill();
   stroke(c,[[x+4,131],[x+33,131]],accent,3);
   stroke(c,[[x+4,148],[x+33,148]],dark,3);
  }
  stroke(c,[[92,168],[243,168],[243,139]],metal,5);
  if(advanced){
   stroke(c,[[225,119],[225,53]],metal,7);
   for(let i=0;i<4;i++)stroke(c,[[221,67+i*12],[229,67+i*12]],dark,2);
   lamp(c,225,50,accent,true);
  }
 }else if(key==="barracks"){
  // Defensive embrasures, reinforced bulkheads and watch positions.
  for(let i=0;i<5;i++){
   const x=104+i*29;
   steel(c,x,120,24,29,metal);
   c.fillStyle="#091b1b";c.fillRect(x+8,130,8,5);
  }
  stroke(c,[[96,115],[242,115]],metal,8);
  for(let i=0;i<8;i++)c.fillRect(101+i*19,106,10,9);
  if(advanced){
   for(const x of [109,225]){
    steel(c,x-11,76,25,39,metal);
    stroke(c,[[x-14,77],[x+17,77]],accent,3);
    lamp(c,x,72,accent,true);
   }
  }
 }
 if(crystal){
  // Crystal Age: sparse emissive conduits, preserving the industrial silhouette.
  c.save();c.shadowColor=accent;c.shadowBlur=12;
  stroke(c,[[110,179],[170,194],[231,178]],accent,2);
  lamp(c,170,194,accent,true);c.restore();
 }
 if(legend){
  polygon(c,[[246,92],[258,66],[270,92],[258,113]],accent,dark);
  stroke(c,[[258,111],[258,150]],metal,3);
  lamp(c,258,66,accent,true);
 }
 c.restore();
}
evolution.draw=function(ctx,left,top,width,height,key,level){
 original(ctx,left,top,width,height,key,level);
 if(!settings.enabled||!settings.details||level<1||!palette[key])return;
 ctx.save();ctx.translate(left,top);ctx.scale(width/340,height/266);
 architecture(ctx,key,level);
 ctx.restore();
};
window.ASHFALL_ARCHITECTURE_87={settings,architecture,version:87};
})();
