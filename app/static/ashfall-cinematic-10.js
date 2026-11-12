/* ASHFALL 10.0 — cinematic world controls; progressive enhancement only. */
(()=>{"use strict";
const root=document.getElementById("world");
if(!root||document.getElementById("af-visual-console"))return;
const mk=(tag,cls,content)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(content!==undefined)e.textContent=content;return e};
const ui=mk("aside","af-visual-console");ui.id="af-visual-console";ui.setAttribute("aria-label","Tactical world display");
const head=mk("div","af-visual-head"),title=mk("strong","","◈ TACTICAL OVERVIEW"),collapse=mk("button","af-visual-toggle","−");collapse.type="button";collapse.setAttribute("aria-label","Collapse tactical overview");collapse.setAttribute("aria-expanded","true");
head.append(title,collapse);ui.append(head);
const body=mk("div","af-visual-body"),mini=document.createElement("canvas");mini.className="af-visual-map";mini.width=320;mini.height=168;mini.tabIndex=0;mini.setAttribute("role","button");mini.setAttribute("aria-label","Tactical map: click or press Enter to reposition the camera");
const caption=mk("div","af-visual-caption"),modeText=mk("span","","SETTLEMENT"),zoomText=mk("span","","ZOOM 100%");caption.append(modeText,zoomText);
const controls=mk("div","af-visual-controls");
function btn(label,description,fn){const b=mk("button","",label);b.type="button";b.title=description;b.setAttribute("aria-label",description);b.onclick=fn;controls.append(b);return b}
const coords=mk("p","af-visual-coordinates","Drag the world to explore. Use the tactical map to reposition.");
body.append(mini,caption,controls,coords);ui.append(body);document.body.append(ui);
// Interactive object inspection uses the same hitboxes as the existing click handler.
const hover=mk("div","af-world-hover");hover.hidden=true;hover.setAttribute("role","status");document.body.append(hover);
let hoverTarget=null;
root.addEventListener("pointermove",e=>{
 const s=state();if(!s||!s.world||typeof objects==="undefined")return;
 if(typeof drag!=="undefined"&&drag){hover.hidden=true;return}
 const x=(e.clientX-innerWidth/2-s.camera.x)/s.camera.zoom;
 const y=(e.clientY-innerHeight/2-s.camera.y)/s.camera.zoom;
 const target=objects.slice().reverse().find(o=>Math.hypot(o.x-x,o.y-y)<o.r);
 hoverTarget=target||null;root.style.cursor=target?"pointer":"grab";
 if(!target){hover.hidden=true;return}
 hover.hidden=false;hover.textContent="⌖ "+target.name+" · CLICK TO INSPECT";
 hover.style.left=Math.min(innerWidth-220,Math.max(10,e.clientX+18))+"px";
 hover.style.top=Math.min(innerHeight-55,Math.max(10,e.clientY+18))+"px";
},{passive:true});
root.addEventListener("pointerleave",()=>{hover.hidden=true;hoverTarget=null});
const toast=mk("div","af-world-toast");toast.hidden=true;toast.setAttribute("role","status");document.body.append(toast);
let toastUntil=0;function announce(s){toast.textContent=s;toast.hidden=false;toastUntil=performance.now()+2100}
collapse.onclick=()=>{const hidden=ui.classList.toggle("af-collapsed");collapse.textContent=hidden?"+":"−";collapse.setAttribute("aria-expanded",String(!hidden))};
const layer=document.createElement("canvas");layer.className="af-vfx-layer";layer.setAttribute("aria-hidden","true");document.body.append(layer);
const vctx=layer.getContext("2d",{alpha:true});if(!vctx)return;
const reduce=window.matchMedia&&window.matchMedia("(prefers-reduced-motion: reduce)").matches;
let effects=!reduce,weather="ASH",quality="HIGH",full=false,wind=0,particles=[],last=0,lastMini=0;
function state(){try{return {camera,mode,world,draw}}catch{return null}}
function resize(){const dpr=Math.min(window.devicePixelRatio||1,1.5);layer.width=Math.round(innerWidth*dpr);layer.height=Math.round(innerHeight*dpr);layer.style.width=innerWidth+"px";layer.style.height=innerHeight+"px";vctx.setTransform(dpr,0,0,dpr,0,0);particles=Array.from({length:quality==="HIGH"?110:55},(_,i)=>({x:(i*149.7)%Math.max(1,innerWidth),y:(i*73.9)%Math.max(1,innerHeight),speed:.45+(i%11)*.09,size:1+(i%4)*.55,phase:i*.73}))}
window.addEventListener("resize",resize,{passive:true});resize();
const effectButton=btn("✦ FX ON","Toggle animated atmospheric effects",()=>{effects=!effects;layer.classList.toggle("af-vfx-off",!effects);effectButton.setAttribute("aria-pressed",String(effects));effectButton.textContent=effects?"✦ FX ON":"✦ FX OFF";announce(effects?"ATMOSPHERE ONLINE":"ATMOSPHERE DISABLED")});
effectButton.setAttribute("aria-pressed",String(effects));
const weatherButton=btn("≋ ASH","Cycle ash, ember and crystal atmospheric effects",()=>{weather=weather==="ASH"?"EMBER":weather==="EMBER"?"CRYSTAL":"ASH";weatherButton.textContent="≋ "+weather;announce(weather+" WEATHER PROFILE")});
const detailButton=btn("▦ HIGH","Toggle atmospheric particle density",()=>{quality=quality==="HIGH"?"LOW":"HIGH";detailButton.textContent="▦ "+quality;resize();announce("VISUAL DETAIL "+quality)});
const architectureButton=btn("▣ DETAIL","Toggle architectural and terrain rendering details",()=>{
 const atelier=window.ASHFALL_RENDER_ATELIER;if(!atelier){announce("RENDER ATELIER NOT LOADED");return}
 atelier.settings.enabled=!atelier.settings.enabled;
 architectureButton.textContent=atelier.settings.enabled?"▣ DETAIL":"▣ SIMPLE";
 architectureButton.setAttribute("aria-pressed",String(atelier.settings.enabled));
 const s=state();if(s)s.draw();
 announce(atelier.settings.enabled?"ARCHITECTURAL DETAIL ONLINE":"SIMPLIFIED RENDERING")
});
architectureButton.setAttribute("aria-pressed","true");
const centerButton=btn("⌖ CENTER","Recenter the world camera",()=>{const s=state();if(!s)return;s.camera.x=0;s.camera.y=0;s.draw();announce("CAMERA RECENTERED")});
const viewButton=btn("⛶ SCREEN","Toggle fullscreen world display",async()=>{try{if(!document.fullscreenElement)await document.documentElement.requestFullscreen();else await document.exitFullscreen()}catch{announce("FULLSCREEN NOT AVAILABLE")}});
const helpButton=btn("? GUIDE","Show world control shortcuts",()=>announce("DRAG TO PAN · SCROLL TO ZOOM · CLICK BUILDINGS · G COMMAND · H IMMERSIVE"));
function noise(x,y){let v=Math.sin(x*12.9898+y*78.233)*43758.5453;return v-Math.floor(v)}
function drawMini(){
 const c=mini.getContext("2d");if(!c)return;const w=mini.width,h=mini.height,s=state();if(!s)return;
 c.clearRect(0,0,w,h);const wilderness=s.mode==="wilderness";
 c.fillStyle=wilderness?"#172a2a":"#1b302c";c.fillRect(0,0,w,h);
 const cell=12;
 for(let x=0;x<Math.ceil(w/cell);x++)for(let y=0;y<Math.ceil(h/cell);y++){
  const n=noise(x+(wilderness?17:5),y+23);
  c.fillStyle=wilderness?(n>.77?"#5b5749":n>.48?"#30473c":"#243b39"):(n>.78?"#52604c":n>.4?"#354b3d":"#293d36");
  c.fillRect(x*cell+1,y*cell+1,cell-2,cell-2)
 }
 c.strokeStyle="#a4b8aa2b";c.lineWidth=1;
 for(let i=0;i<w;i+=24){c.beginPath();c.moveTo(i,0);c.lineTo(i,h);c.stroke()}
 for(let i=0;i<h;i+=24){c.beginPath();c.moveTo(0,i);c.lineTo(w,i);c.stroke()}
 if(!wilderness){
  c.strokeStyle="#baaa80";c.lineWidth=3;c.strokeRect(w*.28,h*.2,w*.44,h*.6);
  c.fillStyle="#bba47b";c.fillRect(w*.46,h*.41,25,18);
  c.fillStyle="#93abb2";for(const [x,y] of [[.37,.33],[.63,.36],[.36,.65],[.63,.66]])c.fillRect(w*x-6,h*y-5,12,10)
 }else{
  for(let i=0;i<18;i++){const x=noise(i,1)*w,y=noise(i,3)*h;c.fillStyle=i%3===0?"#d2a568":"#719e99";c.beginPath();c.arc(x,y,2.5,0,Math.PI*2);c.fill()}
 }
 const px=w/2-s.camera.x/(s.camera.zoom*10),py=h/2-s.camera.y/(s.camera.zoom*10);
 c.strokeStyle="#ffda9b";c.lineWidth=2;c.strokeRect(Math.max(2,Math.min(w-36,px-17)),Math.max(2,Math.min(h-28,py-13)),34,26);
 c.beginPath();c.moveTo(px-7,py);c.lineTo(px+7,py);c.moveTo(px,py-7);c.lineTo(px,py+7);c.stroke();
 modeText.textContent=wilderness?"WILDERNESS":"SETTLEMENT";zoomText.textContent="ZOOM "+Math.round(s.camera.zoom*100)+"%";
 coords.textContent="CAMERA "+Math.round(s.camera.x)+" / "+Math.round(s.camera.y)+"  ·  "+(s.world?.haven?.name||"ASHFALL WORLD")
}
function panMini(x,y){const s=state();if(!s||!s.world)return;s.camera.x=(mini.width/2-x)*s.camera.zoom*10;s.camera.y=(mini.height/2-y)*s.camera.zoom*10;s.draw();drawMini();announce("TACTICAL CAMERA REPOSITIONED")}
mini.addEventListener("click",e=>{const r=mini.getBoundingClientRect();panMini((e.clientX-r.left)/r.width*mini.width,(e.clientY-r.top)/r.height*mini.height)});
mini.addEventListener("keydown",e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();panMini(mini.width/2,mini.height/2)}});
function frame(t){
 if(t-lastMini>200){drawMini();lastMini=t}
 if(effects&&t-last>33){
  const dt=Math.min(2,(t-last||33)/33);last=t;vctx.clearRect(0,0,innerWidth,innerHeight);
  wind=Math.sin(t*.00014)*.7;
  const isCrystal=weather==="CRYSTAL",isEmber=weather==="EMBER";
  for(const p of particles){
   p.x+=(p.speed*(isEmber ? .6 : 1.3)+wind)*dt;p.y+=(p.speed*(isEmber ? -1.8 : 1.1))*dt;
   if(p.x>innerWidth+8)p.x=-8;if(p.x< -8)p.x=innerWidth+8;
   if(p.y>innerHeight+8)p.y=-8;if(p.y< -8)p.y=innerHeight+8;
   const a=.13+.17*(.5+.5*Math.sin(t*.001+p.phase));
   vctx.fillStyle=isCrystal?"rgba(179,145,255,"+a+")":isEmber?"rgba(255,168,87,"+a+")":"rgba(211,190,148,"+a+")";
   vctx.beginPath();vctx.arc(p.x,p.y,p.size*(isCrystal?1.5:1),0,Math.PI*2);vctx.fill()
  }
 }
 requestAnimationFrame(frame)
}
requestAnimationFrame(frame);
document.addEventListener("keydown",e=>{if(e.altKey||e.ctrlKey||e.metaKey||e.target?.closest("input,textarea,select,[contenteditable]"))return;if(e.key.toLowerCase()==="m"&&!e.repeat){collapse.click()}});
})();