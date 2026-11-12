/* ASHFALL — Living Atmosphere 86
   Independent, camera-locked visual layer. No gameplay, hitbox or economy changes.
   30 FPS capped, deterministic particle positions, reduced-motion aware.
*/
(function(){
"use strict";
const main=document.getElementById("world");
if(!main)return;
const canvas=document.createElement("canvas");
canvas.id="ashfall-atmosphere";
canvas.setAttribute("aria-hidden","true");
Object.assign(canvas.style,{position:"fixed",inset:"0",width:"100vw",height:"100vh",zIndex:"1",pointerEvents:"none"});
main.insertAdjacentElement("afterend",canvas);
const ctx=canvas.getContext("2d",{alpha:true});
if(!ctx)return;
const reduced=window.matchMedia("(prefers-reduced-motion: reduce)");
const motion={enabled:!reduced.matches,quality:"high",smoke:true,dust:true,embers:true};
const view={mode:"settlement",camera:{x:0,y:0,zoom:.75},width:innerWidth,height:innerHeight,levels:{}};
let last=0,frame=0,visible=!document.hidden;
const random=n=>{const x=Math.sin(n*127.17+4.9)*43758.5453;return x-Math.floor(x)};
const iso=(x,y)=>({x:(x-y)*64,y:(x+y)*32});
const emitters=[
 {key:"hq",...iso(-3.5,-3.5),height:106,strength:1.1},
 {key:"fuel",...iso(-.5,6),height:68,strength:1.4},
 {key:"salvage",...iso(5.5,4.5),height:65,strength:.65},
 {key:"barracks",...iso(.5,-7),height:72,strength:.5}
];
function resize(){
 const dpr=Math.min(window.devicePixelRatio||1,1.5);
 const w=Math.max(1,Math.round(innerWidth*dpr)),h=Math.max(1,Math.round(innerHeight*dpr));
 if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h}
}
function update(next){
 if(!next)return;
 view.mode=next.mode==="wilderness"?"wilderness":"settlement";
 view.camera={x:Number(next.camera?.x)||0,y:Number(next.camera?.y)||0,zoom:Number(next.camera?.zoom)||1};
 view.width=next.width||innerWidth;view.height=next.height||innerHeight;
 if(next.levels&&typeof next.levels==="object")view.levels=next.levels;
}
function smoke(x,y,t,seed,strength){
 const phase=(t*.000038*strength+random(seed))%1;
 const drift=Math.sin(t*.00035+seed)*7;
 const px=x+phase*58+drift,py=y-phase*125;
 const radius=7+phase*26;
 const alpha=Math.sin(Math.PI*phase)*.13;
 if(alpha<=0)return;
 const grad=ctx.createRadialGradient(px,py,0,px,py,radius);
 grad.addColorStop(0,"rgba(190,178,155,"+alpha.toFixed(3)+")");
 grad.addColorStop(1,"rgba(190,178,155,0)");
 ctx.fillStyle=grad;ctx.beginPath();ctx.arc(px,py,radius,0,Math.PI*2);ctx.fill();
}
function dust(t,w,h){
 const count=motion.quality==="low"?22:65;
 for(let i=0;i<count;i++){
  const x=((random(i+170)*w+t*(.003+random(i+60)*.008))%(w+30))-15;
  const y=random(i+340)*h+Math.sin(t*.0004+i)*7;
  const size=.55+random(i+900)*1.4;
  ctx.fillStyle="rgba(244,183,110,"+(.09+random(i+720)*.17).toFixed(3)+")";
  ctx.beginPath();ctx.arc(x,y,size,0,Math.PI*2);ctx.fill();
 }
}
function draw(t){
 if(!visible)return;
 requestAnimationFrame(draw);
 if(t-last<33)return;
 last=t;
 resize();
 const w=innerWidth,h=innerHeight;
 ctx.setTransform(canvas.width/w,0,0,canvas.height/h,0,0);
 ctx.clearRect(0,0,w,h);
 if(!motion.enabled)return;
 if(motion.dust)dust(t,w,h);
 if(view.mode==="settlement"){
  ctx.save();
  ctx.translate(w/2+view.camera.x,h/2+view.camera.y);
  ctx.scale(view.camera.zoom,view.camera.zoom);
  if(motion.smoke)for(const e of emitters)for(let i=0;i<9;i++)smoke(e.x,e.y-e.height,t,i+e.x*7,e.strength);
  if(motion.embers)for(let i=0;i<23;i++){
   const e=emitters[i%emitters.length],life=(t*.00012+random(i*41))%1;
   const x=e.x+(random(i+72)-.5)*95+life*42;
   const y=e.y-e.height+15-life*105;
   const a=Math.sin(Math.PI*life)*.65;
   ctx.fillStyle="rgba(255,165,79,"+a.toFixed(3)+")";
   ctx.beginPath();ctx.arc(x,y,.8+random(i+88)*1.4,0,Math.PI*2);ctx.fill();
  }
  window.ASHFALL_LIVING_90?.paint(ctx,t,view);
  ctx.restore();
 }
 frame++;
}
function visibility(){visible=!document.hidden;if(visible){last=0;requestAnimationFrame(draw)}}
document.addEventListener("visibilitychange",visibility);
reduced.addEventListener?.("change",e=>{motion.enabled=!e.matches});
window.addEventListener("resize",resize,{passive:true});
window.ASHFALL_ATMOSPHERE={update,settings:motion,version:86};
requestAnimationFrame(draw);
})();
