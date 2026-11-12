/* ASHFALL 29 — Construction command display.
   Uses only server-reported queue data. Completion is never inferred from
   a local countdown: the next successful economy response must confirm it. */
(function(){
"use strict";
let last=null,clockOffset=0,known=false,celebrated=new Set();
const $=id=>document.getElementById(id);
const names={hq:"Command Center",farm:"Farm",lumber:"Lumber Yard",salvage:"Salvage Station",fuel:"Fuel Collector",barracks:"Barracks"};
function ensure(){
 const panel=$("buildpanel");if(!panel)return false;
 if($("afConstruction"))return true;
 const el=document.createElement("div");el.id="afConstruction";
 el.className="af-construction";el.hidden=true;
 el.innerHTML='<div class="af-construction-heading"><strong>CONSTRUCTION COMMAND</strong><span id="afConstructionState">ACTIVE</span></div><div class="af-construction-name" id="afConstructionName"></div><div class="af-construction-track" role="progressbar" aria-label="Construction progress" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0" id="afConstructionTrack"><div id="afConstructionFill"></div></div><div class="af-construction-meta"><span id="afConstructionPercent">0%</span><span id="afConstructionTime">SYNCING</span></div>';
 const queue=$("buildqueue");queue?.insertAdjacentElement("afterend",el);
 return true;
}
function format(seconds){
 const s=Math.max(0,Math.ceil(seconds));
 const h=Math.floor(s/3600),m=Math.floor(s%3600/60),r=s%60;
 return h? h+"h "+String(m).padStart(2,"0")+"m":m?m+"m "+String(r).padStart(2,"0")+"s":r+"s";
}
function tick(){
 if(!ensure())return;
 const box=$("afConstruction");if(!last){box.hidden=true;return}
 box.hidden=false;
 const now=Date.now()/1000+clockOffset;
 const remaining=Math.max(0,Number(last.finishes_at)-now);
 // Queue start is not guaranteed by every API response; avoid fabricated percentages.
 const start=Number(last.started_at??last.starts_at??last.created_at);
 const end=Number(last.finishes_at);
 const validStart=Number.isFinite(start)&&start>0&&start<end;
 const pct=validStart?Math.max(0,Math.min(99.9,(now-start)/(end-start)*100)):null;
 $("afConstructionName").textContent=names[last.building_key]||last.building_key||"Facility";
 $("afConstructionFill").style.width=(pct===null?100:pct)+"%";
 $("afConstructionFill").classList.toggle("indeterminate",pct===null);
 $("afConstructionTrack").setAttribute("aria-valuenow",pct===null?"0":String(Math.floor(pct)));
 $("afConstructionTrack").setAttribute("aria-valuetext",pct===null?"Progress unavailable":Math.floor(pct)+" percent");
 $("afConstructionPercent").textContent=pct===null?"ACTIVE BUILD":"~"+Math.floor(pct)+"%";
 $("afConstructionTime").textContent=remaining>0?format(remaining)+" remaining":"AWAITING SERVER CONFIRMATION";
 $("afConstructionState").textContent=remaining>0?"IN PROGRESS":"VERIFYING";
}
// ASHFALL 30 — server-confirmed milestone reveal; no blocking modal.
const milestoneLevels=[5,15,30,50];
const rewards={
 hq:"Command infrastructure expanded",farm:"Agricultural complex strengthened",
 lumber:"Timber production facility expanded",salvage:"Salvage operations modernized",
 fuel:"Refinery infrastructure expanded",barracks:"Defensive infrastructure strengthened"
};
function reveal(key,level){
 const panel=$("buildpanel");if(!panel)return;
 let notice=$("afConstructionNotice");
 if(!notice){
  notice=document.createElement("section");
  notice.id="afConstructionNotice";notice.className="af-construction-notice";
  notice.setAttribute("role","status");notice.setAttribute("aria-live","polite");
  panel.prepend(notice);
 }
 const isMilestone=milestoneLevels.includes(level);
 notice.classList.toggle("milestone",isMilestone);
 notice.replaceChildren();
 const eyebrow=document.createElement("div");eyebrow.className="af-reveal-eyebrow";
 eyebrow.textContent=isMilestone?"ARCHITECTURAL MILESTONE":"CONSTRUCTION COMPLETE";
 const heading=document.createElement("strong");
 heading.textContent=(names[key]||key)+" · LEVEL "+level;
 const detail=document.createElement("p");
 detail.textContent=isMilestone?(rewards[key]||"Facility evolved")+" — visual tier unlocked.":"Upgrade confirmed by settlement command.";
 const actions=document.createElement("div");actions.className="af-reveal-actions";
 const inspect=document.createElement("button");inspect.type="button";inspect.textContent="Inspect facility";
 inspect.onclick=()=>{if(typeof showBuilding==="function")showBuilding(key);notice.hidden=true;};
 const dismiss=document.createElement("button");dismiss.type="button";dismiss.textContent="Dismiss";
 dismiss.onclick=()=>{notice.hidden=true;};
 actions.append(inspect,dismiss);
 notice.append(eyebrow,heading,detail,actions);notice.hidden=false;
 // A quiet, bounded flourish rather than a disruptive full-screen overlay.
 if(isMilestone&&!window.matchMedia("(prefers-reduced-motion: reduce)").matches){
  notice.classList.remove("af-reveal-enter");
  void notice.offsetWidth;
  notice.classList.add("af-reveal-enter");
 }
}

function sync(data){
 if(!data)return;
 const queue=data.queue||null;
 const server=Number(data.server_time);
 if(Number.isFinite(server))clockOffset=server-Date.now()/1000;
 if(known&&last&&!queue){
  const key=String(last.building_key||"");
  // A cleared queue alone does not prove success; check the reported level.
  const level=Number(data.buildings?.[key]?.level);
  const before=Number(last._observedLevel);
  const signature=key+":"+last.finishes_at;
  if(Number.isFinite(level)&&Number.isFinite(before)&&level>before&&!celebrated.has(signature)){
   celebrated.add(signature);reveal(key,level);
  }
 }
 if(queue){
  const key=String(queue.building_key||"");
  const prior=last&&last.building_key===key&&last.finishes_at===queue.finishes_at?last:null;
  last={...queue,_observedLevel:prior?prior._observedLevel:Number(data.buildings?.[key]?.level)};
 }else last=null;
 known=true;tick();
}
setInterval(tick,1000);
window.ASHFALL_CONSTRUCTION={sync,tick};
})();