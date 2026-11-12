/* ASHFALL 91 — Wilderness Renaissance.
 * Deterministic illustrated biome surfaces, erosion, cliffs, flora, industrial
 * relics and landmark staging. All painting is decorative and world-locked.
 * Server-provided locations, click targets and march routes are untouched.
 */
(function(){
"use strict";
const config={enabled:true,detail:"high",terrain:true,props:true,landmarks:true};
const COLORS={
 forest:{base:"#344d40",light:"#66866a",dark:"#1d332d",soil:"#546049",accent:"#b0a779"},
 scrub:{base:"#4b5844",light:"#798469",dark:"#303d35",soil:"#6a6951",accent:"#b1a47c"},
 ridge:{base:"#625f56",light:"#98917e",dark:"#373d3b",soil:"#76705e",accent:"#b4a287"},
 dust:{base:"#73654e",light:"#b49a71",dark:"#494538",soil:"#8d7759",accent:"#d0b486"}
};
function hash(x,y,s=0){let n=(Math.imul(x|0,374761393)+Math.imul(y|0,668265263)+Math.imul(s|0,2246822519))|0;n=Math.imul(n^(n>>>13),1274126177);return ((n^(n>>>16))>>>0)/4294967296}
function path(c,pts,fill,stroke,width=1){
 c.beginPath();for(let i=0;i<pts.length;i++){const p=pts[i];i?c.lineTo(p[0],p[1]):c.moveTo(p[0],p[1])}
 c.closePath();if(fill){c.fillStyle=fill;c.fill()}if(stroke){c.lineWidth=width;c.strokeStyle=stroke;c.stroke()}
}
function segment(c,x,y,xx,yy,color,width=1){
 c.strokeStyle=color;c.lineWidth=width;c.beginPath();c.moveTo(x,y);c.lineTo(xx,yy);c.stroke();
}
function oval(c,x,y,rx,ry,color){
 c.fillStyle=color;c.beginPath();c.ellipse(x,y,rx,ry,0,0,Math.PI*2);c.fill();
}
function diamond(c,iso,x,y,color){
 const a=iso(x,y),b=iso(x+1,y),d=iso(x+1,y+1),e=iso(x,y+1);
 path(c,[[a.x,a.y],[b.x,b.y],[d.x,d.y],[e.x,e.y]],color);
}
function tile(c,iso,x,y,kind,seed,ox,oy){
 if(!config.enabled||!config.terrain)return false;
 const p=COLORS[kind]||COLORS.scrub;
 const wx=ox+x,wy=oy+y;
 const center=iso(x+.5,y+.5);
 const n=hash(wx,wy,91),n2=hash(wx,wy,14);
 diamond(c,iso,x,y,n<.16?p.dark:n>.86?p.light:p.base);
 // Tiny tonal geometry suggests rock strata, broken earth and vegetation.
 if(kind==="ridge"){
  path(c,[[center.x-44,center.y+10],[center.x-12,center.y-9],[center.x+13,center.y-3],[center.x+36,center.y+12]],p.soil,p.dark,1);
  segment(c,center.x-21,center.y+4,center.x+6,center.y-1,p.light,2);
  if(n>.62)segment(c,center.x+7,center.y+1,center.x+22,center.y+11,p.dark,1.5);
 }else if(kind==="dust"){
  path(c,[[center.x-36,center.y+9],[center.x-8,center.y-4],[center.x+30,center.y+7],[center.x+11,center.y+13]],p.soil);
  for(let i=0;i<3;i++){
   const xx=center.x+(hash(wx,wy,i+7)-.5)*76,yy=center.y+(hash(wx,wy,i+19)-.5)*24;
   segment(c,xx,yy,xx+7+n2*11,yy-2,p.dark,.9);
  }
 }else if(kind==="forest"){
  for(let i=0;i<4;i++){
   const xx=center.x+(hash(wx,wy,i+10)-.5)*90,yy=center.y+(hash(wx,wy,i+40)-.5)*27;
   oval(c,xx,yy,7+hash(wx,wy,i+55)*10,2.5,p.dark);
   segment(c,xx,yy,xx+3,yy-5,p.light,1);
  }
 }else{
  for(let i=0;i<3;i++){
   const xx=center.x+(hash(wx,wy,i+10)-.5)*84,yy=center.y+(hash(wx,wy,i+21)-.5)*27;
   oval(c,xx,yy,3+i*1.5,1.5,i===1?p.light:p.soil);
  }
 }
 // Fractured drainage seams repeat across adjacent world coordinates.
 if(n2>.83){
  segment(c,center.x-23,center.y-6,center.x-8,center.y-1,p.dark,1);
  segment(c,center.x-8,center.y-1,center.x+6,center.y-4,p.dark,1);
 }
 return true;
}
function tree(c,x,y,seed,p){
 const h=31+seed*30;
 oval(c,x+7,y+4,17,5,"rgba(7,17,15,.28)");
 segment(c,x,y,x,y-h*.62,"#554d3e",4);
 for(let i=0;i<3;i++){
  const yy=y-h*.26-i*h*.23,w=18-i*4;
  path(c,[[x-w,yy],[x,yy-h*.52],[x+w,yy]],i%2?p.base:p.dark,p.light,.8);
 }
 segment(c,x-5,y-h*.54,x+3,y-h*.7,p.light,1);
}
function stone(c,x,y,s,p){
 oval(c,x+4,y+3,19*s,5*s,"rgba(9,18,17,.3)");
 path(c,[[x-20*s,y],[x-9*s,y-15*s],[x+6*s,y-21*s],[x+21*s,y-5*s],[x+14*s,y+2*s]],p.soil,p.dark,1);
 path(c,[[x-9*s,y-15*s],[x+6*s,y-21*s],[x+4*s,y-8*s]],p.light);
}
function relic(c,x,y,seed,p){
 const h=18+seed*25;
 oval(c,x+7,y+5,25,6,"rgba(8,18,17,.28)");
 path(c,[[x-21,y],[x-21,y-h],[x+11,y-h-5],[x+19,y-5],[x+19,y]],"#555e58","#263431",2);
 path(c,[[x-18,y-h+3],[x+7,y-h-1],[x+7,y-h+10],[x-18,y-h+14]],"#263b3b","#89918a");
 for(let i=0;i<3;i++)segment(c,x-16+i*9,y-4,x-12+i*9,y-10,p.accent,1);
 segment(c,x+16,y-h,x+23,y-h-13,"#93856b",2);
}
function prop(c,iso,x,y,kind,seed,ox,oy){
 if(!config.enabled||!config.props)return true;
 const p=COLORS[kind]||COLORS.scrub;
 const wx=ox+x,wy=oy+y,roll=hash(wx,wy,99);
 const a=iso(x+.5,y+.5);
 const xx=a.x+(hash(wx,wy,11)-.5)*35,yy=a.y+(hash(wx,wy,12)-.5)*12;
 c.save();c.lineJoin="round";c.lineCap="round";
 if(kind==="forest")tree(c,xx,yy,roll,p);
 else if(kind==="ridge")stone(c,xx,yy,.8+roll*.5,p);
 else if(kind==="dust"){
  if(roll>.68)relic(c,xx,yy,roll,p);
  else {stone(c,xx,yy,.65,p);segment(c,xx-12,yy,xx-6,yy-12,p.accent,1.5)}
 }else if(roll>.78)relic(c,xx,yy,roll,p);
 else{
  oval(c,xx,yy+2,13,4,"rgba(8,22,18,.25)");
  for(let i=0;i<5;i++)segment(c,xx+(i-2)*3,yy,xx+(i-2)*4,yy-6-hash(wx,wy,i)*9,p.light,1.5);
 }
 c.restore();return true;
}
function landmark(c,iso,x,y,kind){
 if(!config.enabled||!config.landmarks)return;
 const p=iso(x,y),color=kind==="ENCOUNTER"?"rgba(219,123,88,.15)":kind==="GATHERING SITE"?"rgba(119,186,147,.14)":"rgba(221,175,111,.13)";
 c.save();
 oval(c,p.x,p.y+5,47,20,"rgba(4,14,15,.34)");
 oval(c,p.x,p.y+3,36,13,color);
 for(let i=0;i<8;i++){
  const a=i*Math.PI/4;
  segment(c,p.x+Math.cos(a)*39,p.y+Math.sin(a)*16,p.x+Math.cos(a)*46,p.y+Math.sin(a)*19,"rgba(208,192,150,.25)",1);
 }
 c.restore();
}
window.ASHFALL_WILDERNESS_91={tile,prop,landmark,settings:config,version:91};
})();
