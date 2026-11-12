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
window.ASHFALL_ART_EVOLUTION={draw,config,tiers:[5,15,30,50]};
})();