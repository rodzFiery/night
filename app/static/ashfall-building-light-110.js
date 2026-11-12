/* ASHFALL 110 — physically grounded building presentation.
   World-space contact occlusion, directional silhouette shadow and warm/cool
   material light response. The silhouette uses the actual sprite alpha.
   No artificial geometry replacing authored building images. */
(function(){
"use strict";
const settings={enabled:true,shadow:true,contact:true,ambient:true,quality:"high"};
function ground(ctx,x,y,w,h,key,level){
 if(!settings.enabled)return;
 ctx.save();
 if(settings.contact){
  // Wide, soft contact occlusion binds sprite to the terrain.
  const gradient=ctx.createRadialGradient(x,y,5,x,y,w*.48);
  gradient.addColorStop(0,"rgba(2,8,10,.55)");
  gradient.addColorStop(.55,"rgba(2,8,10,.27)");
  gradient.addColorStop(1,"rgba(2,8,10,0)");
  ctx.fillStyle=gradient;
  ctx.beginPath();ctx.ellipse(x,y+5,w*.48,h*.20,0,0,Math.PI*2);ctx.fill();
 }
 if(settings.ambient){
  const crystal=level>25;
  const glow=ctx.createRadialGradient(x,y,1,x,y,w*.43);
  glow.addColorStop(0,crystal?"rgba(81,150,215,.14)":"rgba(219,155,86,.12)");
  glow.addColorStop(1,"rgba(0,0,0,0)");
  ctx.fillStyle=glow;ctx.beginPath();ctx.ellipse(x,y+7,w*.45,h*.18,0,0,Math.PI*2);ctx.fill();
 }
 ctx.restore();
}
function silhouette(ctx,img,left,top,w,h){
 if(!settings.enabled||!settings.shadow)return;
 // A single alpha-based shadow pass is much more believable than rectangles
 // or detached geometric shadows. Skew into the ground plane.
 ctx.save();
 ctx.globalAlpha=.20;
 ctx.filter="brightness(0)";
 ctx.translate(left+w*.57,top+h*.91);
 ctx.transform(1,0,-.44,.27,0,0);
 ctx.drawImage(img,-w*.5,-h*.93,w,h);
 ctx.restore();
}
function material(ctx,left,top,w,h,level){
 // Do not paint a rectangular lighting gradient over transparent artwork:
 // the rectangle is visible against the ground and undermines authored art.
 // Ground bounce and sprite-based shadows already supply world integration.
 // Future material grading must be alpha-masked to the actual sprite.
}

window.ASHFALL_BUILDING_LIGHT_110=Object.freeze({ground,silhouette,material,settings});
})();