/* ASHFALL 90 — Living Settlement Atelier
   Canvas embellishments rendered inside the existing 86 atmosphere loop.
   Visual only. No extra animation scheduler, hit targets or gameplay writes.
*/
(function(){
"use strict";
const settings={enabled:true,machinery:true,beacons:true,vegetation:true,quality:"high"};
const iso=(x,y)=>({x:(x-y)*64,y:(x+y)*32});
const sites=[
 {key:"hq",...iso(-3.5,-3.5),height:114},
 {key:"farm",...iso(4.5,-5),height:70},
 {key:"lumber",...iso(-5.5,3),height:79},
 {key:"salvage",...iso(5.5,4.5),height:100},
 {key:"fuel",...iso(-.5,6),height:91},
 {key:"barracks",...iso(.5,-7),height:102}
];
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
function line(ctx,x1,y1,x2,y2,color,width=2){
 ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);
 ctx.strokeStyle=color;ctx.lineWidth=width;ctx.stroke();
}
function lamp(ctx,x,y,color,brightness){
 ctx.save();ctx.globalAlpha=clamp(brightness,0,1);
 ctx.fillStyle=color;ctx.shadowColor=color;ctx.shadowBlur=12;
 ctx.beginPath();ctx.arc(x,y,2.6,0,Math.PI*2);ctx.fill();ctx.restore();
}
function wheel(ctx,x,y,r,angle){
 ctx.save();ctx.translate(x,y);ctx.rotate(angle);
 ctx.strokeStyle="#9aaba6";ctx.lineWidth=2.4;
 ctx.beginPath();ctx.arc(0,0,r,0,Math.PI*2);ctx.stroke();
 for(let i=0;i<6;i++){
  const a=i*Math.PI/3;
  line(ctx,0,0,Math.cos(a)*r,Math.sin(a)*r,"#c3b59b",1.4);
 }
 ctx.fillStyle="#303c3a";ctx.beginPath();ctx.arc(0,0,3,0,Math.PI*2);ctx.fill();
 ctx.restore();
}
function vegetation(ctx,t,low){
 const count=low?12:28;
 for(let i=0;i<count;i++){
  const a=i*2.39996,dist=670+(i%7)*68;
  const x=Math.cos(a)*dist,y=Math.sin(a)*dist*.65;
  const sway=Math.sin(t*.0006+i*2.1)*2.5;
  line(ctx,x,y,x+sway,y-10-(i%4)*3,"rgba(132,158,112,.48)",1.4);
  line(ctx,x+sway,y-9,x+sway+4,y-13,"rgba(161,174,126,.45)",1);
 }
}
function paint(ctx,t,view){
 if(!settings.enabled||view?.mode!=="settlement")return;
 const low=settings.quality==="low",levels=view.levels||{};
 ctx.save();ctx.lineCap="round";
 if(settings.vegetation)vegetation(ctx,t,low);
 for(const s of sites){
  const level=Number(levels[s.key]??0);
  if(level<=0)continue;
  const x=s.x,y=s.y-s.height;
  if(settings.beacons){
   const pulse=.65+.35*Math.sin(t*.002+s.x);
   lamp(ctx,x+38,y+18,s.key==="salvage"?"#91e0dc":"#ffc080",pulse);
  }
  if(!settings.machinery)continue;
  if(s.key==="lumber"){
   wheel(ctx,x-20,y+34,12,t*.0004);
   line(ctx,x-20,y+34,x+13,y+22,"rgba(177,161,129,.75)",2);
  }else if(s.key==="salvage"){
   const offset=Math.sin(t*.0007)*7;
   line(ctx,x-35,y+22,x+32,y+22,"#a1b9b7",3);
   line(ctx,x+offset,y+22,x+offset,y+49,"#8db3af",2);
   ctx.fillStyle="#718c8c";ctx.fillRect(x+offset-9,y+46,18,6);
  }else if(s.key==="fuel"){
   const pressure=.5+.5*Math.sin(t*.001);
   lamp(ctx,x+20,y+8,"#f7b36f",pressure);
  }else if(s.key==="farm"){
   for(let i=0;i<3;i++){
    const dx=x-22+i*22;
    line(ctx,dx,y+55,dx+Math.sin(t*.0005+i)*3,y+46,"rgba(159,202,144,.75)",2);
   }
  }else if(s.key==="hq"&&level>=15){
   const a=t*.0002;
   line(ctx,x+3,y+10,x+3+Math.cos(a)*22,y+10+Math.sin(a)*6,"rgba(250,186,111,.6)",1.5);
  }else if(s.key==="barracks"){
   lamp(ctx,x-30,y+25,"#f1a58a",.7+.3*Math.sin(t*.0012));
  }
 }
 ctx.restore();
}
window.ASHFALL_LIVING_90={paint,settings,version:90};
})();
