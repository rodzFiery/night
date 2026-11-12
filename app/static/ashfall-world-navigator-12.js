/* ASHFALL 12 — World interaction and cinematic camera.
   Works with the authoritative objects array produced by the Living World renderer. */
(()=>{"use strict";
const root=document.getElementById("world");if(!root||document.getElementById("af-world-navigator"))return;
const $=(tag,cls,content)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(content!==undefined)e.textContent=content;return e};
const nav=$("aside","af-world-navigator");nav.id="af-world-navigator";nav.setAttribute("aria-label","World object navigator");
const top=$("div","af-nav-top"),heading=$("strong","","⌖ WORLD NAVIGATOR"),toggle=$("button","af-nav-toggle","−");toggle.type="button";toggle.setAttribute("aria-expanded","true");toggle.setAttribute("aria-label","Collapse world navigator");top.append(heading,toggle);nav.append(top);
const body=$("div","af-nav-body"),filter=$("input","af-nav-filter");filter.type="search";filter.placeholder="Find buildings and locations";filter.setAttribute("aria-label","Search world objects");
const list=$("div","af-nav-list");list.setAttribute("role","list");
const count=$("div","af-nav-count","WORLD OBJECTS · SYNCING");
body.append(filter,count,list);nav.append(body);document.body.append(nav);
toggle.onclick=()=>{const collapsed=nav.classList.toggle("af-nav-collapsed");toggle.textContent=collapsed?"+":"−";toggle.setAttribute("aria-expanded",String(!collapsed))};
const reduced=matchMedia("(prefers-reduced-motion: reduce)").matches;
let selected=null,focused=null,animation=0,previous="",lastMode="",lastObjects=[];
function access(){try{return {camera,objects,mode,world,draw,showBuilding}}catch{return null}}
function focusObject(o){
 const s=access();if(!s||!s.world)return;
 selected=o.name;focused={name:o.name,x:o.x,y:o.y};
 const targetX=-o.x*s.camera.zoom,targetY=-o.y*s.camera.zoom;
 cancelAnimationFrame(animation);
 const startX=s.camera.x,startY=s.camera.y,start=performance.now(),duration=reduced?0:580;
 function frame(t){const p=duration?Math.min(1,(t-start)/duration):1,k=1-Math.pow(1-p,3);s.camera.x=startX+(targetX-startX)*k;s.camera.y=startY+(targetY-startY)*k;s.draw();if(p<1)animation=requestAnimationFrame(frame)}
 animation=requestAnimationFrame(frame);
 if(s.mode==="settlement"&&o.buildingKey&&typeof s.showBuilding==="function")s.showBuilding(o.buildingKey);
 const info=document.getElementById("info");if(info){const kind=document.getElementById("kind"),name=document.getElementById("selected"),detail=document.getElementById("detail");if(kind)kind.textContent=o.kind||"WORLD OBJECT";if(name)name.textContent=o.name;if(detail)detail.textContent=o.detail||"";info.hidden=false}
 if(s.mode==="wilderness"&&o.action){const actionMap={expeditions:"expeditionButton",combat:"combatButton",events:"eventsButton"};const button=document.getElementById(actionMap[o.action]);if(button)button.click()}
 refresh(true)
}
function refresh(force=false){
 const s=access();if(!s||!s.world)return;
 const q=filter.value.toLowerCase().trim();
 const all=s.objects.filter(o=>o&&o.name&&Number.isFinite(o.x)&&Number.isFinite(o.y));
 const fingerprint=s.mode+"|"+q+"|"+all.map(o=>o.name+":"+(o.buildingKey||o.kind||"")).join(",");
 if(!force&&fingerprint===previous)return;
 previous=fingerprint;
 const visible=all.filter(o=>o.name.toLowerCase().includes(q)||(o.kind||"").toLowerCase().includes(q)).slice(0,90);
 list.replaceChildren();count.textContent=(s.mode==="settlement"?"SETTLEMENT":"WILDERNESS")+" · "+all.length+" OBJECTS";
 if(!visible.length)list.append($("p","af-nav-empty","No matching locations."));
 for(const o of visible){
  const b=$("button","af-nav-item");b.type="button";
  b.setAttribute("aria-label","Focus "+o.name);
  if(o.name===selected)b.classList.add("af-nav-selected");
  const mark=$("span","af-nav-mark",o.buildingKey?"▣":o.kind==="ENCOUNTER"?"◇":"⌖");
  const copy=$("span","af-nav-copy"),name=$("strong","",o.name),meta=$("small","",(o.kind||"LOCATION")+" · CLICK TO FOCUS");
  copy.append(name,meta);b.append(mark,copy);b.onclick=()=>focusObject(o);list.append(b)
 }
 if(lastMode!==s.mode){lastMode=s.mode;selected=null;focused=null}
}
filter.addEventListener("input",()=>refresh(true));
let lastDraw=0;
function renderSelection(t){
 const s=access();if(!s||!s.world||!focused)return;
 const overlay=document.getElementById("af-selection-overlay");
 if(!overlay)return;
 const dpr=Math.min(devicePixelRatio||1,1.5),w=innerWidth,h=innerHeight;
 if(overlay.width!==Math.round(w*dpr)||overlay.height!==Math.round(h*dpr)){overlay.width=Math.round(w*dpr);overlay.height=Math.round(h*dpr)}
 const c=overlay.getContext("2d");if(!c)return;
 c.setTransform(dpr,0,0,dpr,0,0);c.clearRect(0,0,w,h);
 const o=s.objects.find(v=>v.name===focused.name&&Math.abs(v.x-focused.x)<1&&Math.abs(v.y-focused.y)<1);
 if(!o){focused=null;return}
 const x=w/2+s.camera.x+o.x*s.camera.zoom,y=h/2+s.camera.y+o.y*s.camera.zoom;
 if(x< -100||x>w+100||y< -100||y>h+100)return;
 const pulse=reduced?0:.5+.5*Math.sin(t*.004),r=Math.max(28,Math.min(62,(o.r||48)*s.camera.zoom))+(pulse*5);
 c.strokeStyle="#f7c98a";c.lineWidth=2;c.shadowColor="#f5b86e";c.shadowBlur=12;
 c.beginPath();c.ellipse(x,y+11*s.camera.zoom,r,r*.37,0,0,Math.PI*2);c.stroke();
 c.shadowBlur=0;
 for(const angle of [0,Math.PI/2,Math.PI,Math.PI*1.5]){const ax=x+Math.cos(angle)*r,ay=y+11*s.camera.zoom+Math.sin(angle)*r*.37;c.fillStyle="#ffe0a5";c.fillRect(ax-2,ay-2,4,4)}
 c.fillStyle="#f5d7aa";c.font="bold 11px Segoe UI, sans-serif";c.textAlign="center";c.fillText("◆ "+o.name.toUpperCase(),x,y-r*.55-18)
}
const overlay=$("canvas","af-selection-overlay");overlay.id="af-selection-overlay";overlay.setAttribute("aria-hidden","true");document.body.append(overlay);
function loop(t){if(t-lastDraw>250){refresh();lastDraw=t}renderSelection(t);requestAnimationFrame(loop)}
requestAnimationFrame(loop);
root.addEventListener("pointerup",e=>{if(typeof moved!=="undefined"&&moved)return;const s=access();if(!s)return;const x=(e.clientX-innerWidth/2-s.camera.x)/s.camera.zoom,y=(e.clientY-innerHeight/2-s.camera.y)/s.camera.zoom;const o=s.objects.slice().reverse().find(o=>Math.hypot(o.x-x,o.y-y)<o.r);if(o){selected=o.name;focused={name:o.name,x:o.x,y:o.y};refresh(true)}});
document.addEventListener("keydown",e=>{if(e.altKey||e.ctrlKey||e.metaKey||e.target?.closest("input,textarea,select,[contenteditable]"))return;if(e.key.toLowerCase()==="n"&&!e.repeat){toggle.click()}});
})();