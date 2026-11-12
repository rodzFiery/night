/* ASHFALL 25 — Architectural evolution overlay.
   Deterministic, level-gated visual identity for all six facilities.
   Coordinates are normalized to the existing sprite image bounds.
   No gameplay values or building hitboxes are modified. */
(function(){
"use strict";
const config={enabled:true,details:true,beacons:true};
const themes={
 hq:{metal:"#b6c5bf",accent:"#efb66e",dark:"#344c55"},
 farm:{metal:"#9cad8d",accent:"#d4d77b",dark:"#3d5943"},
 lumber:{metal:"#c0a27b",accent:"#e5ac65",dark:"#5b453b"},
 salvage:{metal:"#a2b8b9",accent:"#8fe2dd",dark:"#3d555b"},
 fuel:{metal:"#a4bb9d",accent:"#d7bd74",dark:"#43564c"},
 barracks:{metal:"#c5a29b",accent:"#e8a086",dark:"#58474a"}
};
function line(ctx,x1,y1,x2,y2,color,width=2){
 ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.lineWidth=width;ctx.strokeStyle=color;ctx.stroke();
}
function panel(ctx,x,y,w,h,t){
 ctx.fillStyle=t.dark;ctx.fillRect(x,y,w,h);
 ctx.fillStyle=t.metal;ctx.fillRect(x+2,y+2,w-4,h-4);
 ctx.fillStyle="#20353d";ctx.fillRect(x+5,y+5,w-10,h-10);
 line(ctx,x+w*.5,y+5,x+w*.5,y+h-5,t.metal,1.5);
 line(ctx,x+5,y+h*.5,x+w-5,y+h*.5,t.metal,1.5);
}

// ASHFALL 26 — recognizable architectural identity for every facility.
// These features are intentionally legible at normal camera zoom.
function identity(ctx,key,t,level){
 if(level<15)return;
 ctx.save();
 ctx.lineJoin="round";ctx.lineCap="round";
 if(key==="farm"){
  // A pair of elevated greenhouse tunnels and agricultural irrigation lines.
  for(const x of [96,164]){
   ctx.fillStyle="rgba(113,179,143,.35)";
   ctx.beginPath();ctx.moveTo(x,111);ctx.quadraticCurveTo(x+23,70,x+46,111);
   ctx.lineTo(x+46,127);ctx.lineTo(x,127);ctx.closePath();ctx.fill();
   line(ctx,x,111,x+23,81,t.metal,3);
   line(ctx,x+23,81,x+46,111,t.metal,3);
   for(let i=1;i<4;i++)line(ctx,x+i*11,105,x+i*11,125,"rgba(211,235,188,.65)",1.5);
  }
  if(level>=30){line(ctx,82,140,238,140,t.accent,4);}
 }else if(key==="lumber"){
  // Crane arm, suspended timber and sawmill roof silhouette.
  line(ctx,118,127,118,47,t.metal,6);
  line(ctx,118,49,234,72,t.metal,5);
  line(ctx,118,49,97,77,t.metal,3);
  line(ctx,216,69,216,111,t.dark,2);
  ctx.fillStyle="#b88c58";ctx.fillRect(190,112,56,14);
  for(let i=0;i<3;i++)line(ctx,193,115+i*4,241,115+i*4,"#e2b47a",1.5);
  if(level>=30){ctx.fillStyle=t.accent;ctx.fillRect(125,57,8,8);}
 }else if(key==="salvage"){
  // Magnetic salvage gantry with overhead crossbeam.
  line(ctx,92,146,92,57,t.metal,7);
  line(ctx,247,146,247,57,t.metal,7);
  line(ctx,92,58,247,58,t.metal,8);
  for(let x=111;x<240;x+=24)line(ctx,x,54,x+12,63,t.dark,3);
  line(ctx,177,61,177,109,t.dark,3);
  ctx.fillStyle=t.accent;ctx.fillRect(156,107,42,11);
  ctx.fillStyle=t.dark;ctx.fillRect(162,118,30,10);
  if(level>=30){ctx.shadowColor=t.accent;ctx.shadowBlur=10;line(ctx,163,112,192,112,t.accent,3);ctx.shadowBlur=0;}
 }else if(key==="fuel"){
  // Elevated refinery vessels, connecting pipes and vent stacks.
  for(const x of [116,193]){
   ctx.fillStyle=t.metal;ctx.fillRect(x,86,34,69);
   ctx.fillStyle=t.dark;ctx.beginPath();ctx.ellipse(x+17,86,17,8,0,0,Math.PI*2);ctx.fill();
   line(ctx,x+4,116,x+30,116,t.accent,3);
   line(ctx,x+4,143,x+30,143,t.dark,2);
  }
  line(ctx,150,125,193,125,t.metal,6);
  line(ctx,224,109,224,49,t.metal,7);
  if(level>=30){ctx.fillStyle="rgba(244,191,109,.75)";ctx.beginPath();ctx.arc(224,47,5,0,Math.PI*2);ctx.fill();}
 }else if(key==="barracks"){
  // Fortified watchtowers and armored parapet.
  for(const x of [88,220]){
   ctx.fillStyle=t.dark;ctx.fillRect(x,85,30,71);
   ctx.fillStyle=t.metal;ctx.fillRect(x-5,80,40,13);
   for(let i=0;i<3;i++)ctx.fillRect(x+i*12,70,7,12);
   ctx.fillStyle="#1d292f";ctx.fillRect(x+9,106,12,17);
  }
  line(ctx,117,138,220,138,t.metal,7);
  if(level>=30){for(let i=0;i<5;i++)ctx.fillRect(131+i*18,129,10,10);}
 }else if(key==="hq"){
  // Command spire, rooftop sensor dish and network uplink.
  line(ctx,172,119,172,39,t.metal,6);
  line(ctx,172,41,205,20,t.accent,3);
  ctx.strokeStyle=t.metal;ctx.lineWidth=4;
  ctx.beginPath();ctx.ellipse(208,30,28,10,-.35,0,Math.PI);ctx.stroke();
  line(ctx,206,29,213,17,t.accent,2);
  if(level>=30){ctx.shadowColor=t.accent;ctx.shadowBlur=14;ctx.fillStyle=t.accent;ctx.beginPath();ctx.arc(213,17,5,0,Math.PI*2);ctx.fill();ctx.shadowBlur=0;}
 }
 ctx.restore();
}

function draw(ctx,left,top,width,height,key,level){
 if(!config.enabled||level<5)return;
 const t=themes[key];if(!t)return;
 ctx.save();ctx.translate(left,top);ctx.scale(width/340,height/266);
 // Each evolution tier is additive and intentionally occupies the upper
 // portion of the existing sprite so the building footprint stays unchanged.
 if(level>=5&&config.details){
  // Reinforced rooftop parapets and structural service hatches.
  line(ctx,95,115,164,81,t.metal,3);
  line(ctx,164,81,232,115,t.metal,3);
  panel(ctx,143,102,39,23,t);
  ctx.fillStyle=t.accent;
  for(let i=0;i<4;i++)ctx.fillRect(103+i*10,130,5,2);
 }
 if(level>=15){
  // Communications equipment, elevated maintenance mast and aerial.
  line(ctx,218,117,218,55,t.metal,4);
  line(ctx,218,55,218,32,t.accent,2);
  line(ctx,201,73,235,73,t.metal,3);
  line(ctx,205,82,231,82,t.metal,2);
  line(ctx,218,59,201,82,t.dark,1.6);
  line(ctx,218,59,235,82,t.dark,1.6);
  ctx.fillStyle=t.accent;ctx.beginPath();ctx.arc(218,31,4,0,Math.PI*2);ctx.fill();
 }
 if(level>=30){
  // Tier III: facility-specific energy and identity lighting.
  ctx.shadowColor=t.accent;ctx.shadowBlur=11;
  line(ctx,110,151,167,180,t.accent,3);
  line(ctx,167,180,224,150,t.accent,3);
  ctx.shadowBlur=0;
  panel(ctx,121,111,28,15,t);
  panel(ctx,186,112,28,15,t);
 }
 identity(ctx,key,t,level);
 if(level>=50){
  // Tier IV: expanded roof hardware and signature pennant.
  line(ctx,122,105,122,46,t.metal,3);
  ctx.fillStyle=t.accent;
  ctx.beginPath();ctx.moveTo(124,47);ctx.lineTo(161,57);ctx.lineTo(124,71);ctx.closePath();ctx.fill();
  line(ctx,119,46,119,103,t.dark,2);
  ctx.fillStyle=t.metal;ctx.fillRect(173,97,38,6);
  ctx.fillStyle=t.dark;ctx.fillRect(179,91,25,6);
 }
 ctx.restore();
}
window.ASHFALL_ART_EVOLUTION={draw,config,tiers:[5,15,30,50],version:26};
})();