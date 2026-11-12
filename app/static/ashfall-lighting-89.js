/* ASHFALL 89 — Cinematic Lighting Atelier
   Art-only world-space light and contact-shadow pass.
   All geometry is deterministic and tied to existing building footprints.
   No time-of-day mechanics, simulation changes, or additional animation loop.
*/
(function(){
"use strict";
const settings={enabled:true,shadows:true,lighting:true,atmosphere:true,quality:"high"};
const tones={
 hq:["255,186,111",1.15],farm:["198,221,146",.55],
 lumber:["250,174,100",.7],salvage:["132,214,211",.75],
 fuel:["255,171,94",1],barracks:["255,162,118",.8]
};
function ellipse(ctx,x,y,rx,ry,color){
 ctx.fillStyle=color;ctx.beginPath();ctx.ellipse(x,y,rx,ry,0,0,Math.PI*2);ctx.fill();
}
function softLight(ctx,x,y,rx,ry,rgb,strength){
 ctx.save();ctx.translate(x,y);ctx.scale(1,ry/rx);
 const gradient=ctx.createRadialGradient(0,0,0,0,0,rx);
 gradient.addColorStop(0,"rgba("+rgb+","+(strength*.26).toFixed(3)+")");
 gradient.addColorStop(.4,"rgba("+rgb+","+(strength*.09).toFixed(3)+")");
 gradient.addColorStop(1,"rgba("+rgb+",0)");
 ctx.fillStyle=gradient;ctx.beginPath();ctx.arc(0,0,rx,0,Math.PI*2);ctx.fill();ctx.restore();
}
function underlay(ctx,b,key,level){
 if(!settings.enabled||!b)return;
 const iso=(x,y)=>({x:(x-y)*64,y:(x+y)*32});
 const center=iso(b.x+b.w/2,b.y+b.h/2);
 const width=(b.w+b.h)*40;
 const height=(b.w+b.h)*17;
 ctx.save();
 // The building's existing ground footprint is never altered.
 if(settings.shadows){
  ellipse(ctx,center.x+12,center.y+13,width*.72,height*.78,"rgba(3,12,13,.22)");
  // Soft directional cast shadow, southwest of the existing sprite.
  const heightScale=Math.min(1.55,.65+Math.max(0,level)*.014);
  const dx=44*heightScale,dy=25*heightScale;
  const grad=ctx.createLinearGradient(center.x,center.y,center.x+dx,center.y+dy);
  grad.addColorStop(0,"rgba(2,10,12,.35)");
  grad.addColorStop(1,"rgba(2,10,12,0)");
  ctx.fillStyle=grad;
  ctx.beginPath();ctx.moveTo(center.x-width*.34,center.y-10);
  ctx.lineTo(center.x+width*.30,center.y-10);
  ctx.lineTo(center.x+width*.30+dx,center.y+dy);
  ctx.lineTo(center.x-width*.34+dx,center.y+dy);ctx.closePath();ctx.fill();
 }
 if(settings.lighting&&level>0){
  const [rgb,intensity]=tones[key]||tones.hq;
  const strength=intensity*(level>=30?1.2:level>=15?.85:.55);
  softLight(ctx,center.x,center.y-15,width*.88,height*1.45,rgb,strength);
  if(level>=15){
   softLight(ctx,center.x+width*.24,center.y-height*.55,width*.28,height*.55,rgb,strength*.65);
  }
 }
 ctx.restore();
}
function foreground(ctx,w,h,mode){
 if(!settings.enabled||!settings.atmosphere||mode!=="settlement")return;
 ctx.save();
 ctx.setTransform(ctx.canvas.width/w,0,0,ctx.canvas.height/h,0,0);
 const sun=ctx.createRadialGradient(w*.22,h*.14,0,w*.22,h*.14,Math.max(w,h)*.9);
 sun.addColorStop(0,"rgba(243,174,100,.065)");
 sun.addColorStop(.4,"rgba(210,147,83,.024)");
 sun.addColorStop(1,"rgba(22,34,32,0)");
 ctx.fillStyle=sun;ctx.fillRect(0,0,w,h);
 const haze=ctx.createLinearGradient(0,h*.38,0,h);
 haze.addColorStop(0,"rgba(135,151,132,0)");
 haze.addColorStop(1,"rgba(116,135,120,.075)");
 ctx.fillStyle=haze;ctx.fillRect(0,0,w,h);
 ctx.restore();
}
window.ASHFALL_LIGHTING_89={underlay,foreground,settings,version:89};
})();
