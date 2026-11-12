/* ASHFALL 39 — Development Strategy.
   Explainable, read-only priorities using current authoritative economy data.
   No assumptions about future prices, combat strength, or production gains. */
(function(){
"use strict";
const $=id=>document.getElementById(id);
const keys=["hq","farm","lumber","salvage","fuel","barracks"];
const milestones=[5,15,30,50];
let data=null,selected=null,focus="balanced";
const focusLabels={balanced:"Balanced",economy:"Production",milestones:"Architecture"};
function analyze(key){
 const b=data?.buildings?.[key];if(!b)return null;
 const level=Math.max(0,Number(b.level)||0);
 const max=level>=55;
 const costs=Object.entries({...b.cost,...b.rare_cost}).filter(([,v])=>Number(v)>0);
 const shortages=costs.map(([resource,raw])=>{
  const stock=Object.prototype.hasOwnProperty.call(data.resources||{},resource)?data.resources?.[resource]:data.rare_materials?.[resource];
  return {resource,missing:Math.max(0,Number(raw)-(Number(stock)||0))};
 }).filter(x=>x.missing>0);
 const next=milestones.find(v=>v>level)||null;
 const distance=next===null?Infinity:next-level;
 const production=Boolean(b.resource)&&Number(b.rate)>0;
 const queue=data.queue?.building_key;
 const status=max?"MAX LEVEL":queue===key?"UNDER CONSTRUCTION":queue?"SLOT OCCUPIED":shortages.length?"RESOURCES NEEDED":"READY";
 // Ranking is a transparent heuristic, NOT a server recommendation or a forecast.
 let score=0;
 if(!max&&queue!==key){
  if(status==="READY")score+=40;
  if(distance===1)score+=30;
  else if(distance<=3)score+=15;
  if(production)score+=focus==="economy"?32:focus==="balanced"?12:0;
  if(focus==="milestones"&&Number.isFinite(distance))score+=Math.max(0,32-distance*2);
  if(key==="hq"&&focus==="balanced")score+=8;
  if(shortages.length)score-=Math.min(30,shortages.length*10);
  if(queue)score-=15;
 }
 return {key,name:b.name||key,level,score,status,distance,next,production,shortages};
}
function ensure(){
 const panel=$("buildpanel");if(!panel)return null;
 let root=$("afStrategy39");if(root)return root;
 root=document.createElement("section");root.id="afStrategy39";root.className="af-strategy39";
 root.setAttribute("aria-label","Development strategy planner");
 const title=document.createElement("div");title.className="af-strategy-head39";
 const label=document.createElement("strong");label.textContent="DEVELOPMENT STRATEGY";
 const tag=document.createElement("span");tag.textContent="ADVISORY · NO AUTO-BUILD";
 title.append(label,tag);
 const controls=document.createElement("div");controls.className="af-strategy-controls39";
 for(const [value,name] of Object.entries(focusLabels)){
  const btn=document.createElement("button");btn.type="button";btn.dataset.afStrategy=value;
  btn.textContent=name;btn.onclick=()=>{focus=value;render()};
  controls.append(btn);
 }
 const explanation=document.createElement("p");explanation.id="afStrategyExplanation39";
 const list=document.createElement("div");list.id="afStrategyList39";list.className="af-strategy-list39";
 const foot=document.createElement("p");foot.className="af-strategy-foot39";
 foot.textContent="Suggestions use current building levels, stock and upgrade costs. Rankings are advisory heuristics, not guaranteed returns.";
 root.append(title,controls,explanation,list,foot);
 const priorities=$("afPriorities38");
 if(priorities)priorities.insertAdjacentElement("afterend",root);
 else panel.append(root);
 return root;
}
function render(){
 if(!data||!ensure())return;
 for(const button of document.querySelectorAll("[data-af-strategy]"))
  button.setAttribute("aria-pressed",String(button.dataset.afStrategy===focus));
 $("afStrategyExplanation39").textContent={
  balanced:"Balance immediate affordability, near-term architecture and productive facilities.",
  economy:"Favor facilities with reported resource production. Future output increases are unknown.",
  milestones:"Favor buildings near the next visual evolution threshold."
 }[focus];
 const ranked=keys.map(analyze).filter(Boolean).filter(x=>x.status!=="MAX LEVEL");
 ranked.sort((a,b)=>b.score-a.score||keys.indexOf(a.key)-keys.indexOf(b.key));
 const list=$("afStrategyList39");list.replaceChildren();
 if(!ranked.length){const p=document.createElement("p");p.textContent="All available facilities are at maximum level.";list.append(p)}
 for(const [index,item] of ranked.slice(0,3).entries()){
  const button=document.createElement("button");button.type="button";button.className="af-strategy-item39";
  button.setAttribute("aria-pressed",String(selected===item.key));
  const heading=document.createElement("strong");heading.textContent="#"+(index+1)+" "+item.name+" · LV "+item.level;
  const state=document.createElement("span");state.textContent=item.status;
  const detail=document.createElement("small");
  const parts=[];
  if(item.next!==null)parts.push("Visual milestone LV "+item.next+" · "+item.distance+" levels away");
  if(item.production)parts.push("Reported production facility");
  if(item.shortages.length)parts.push(item.shortages.map(s=>s.resource.replaceAll("_"," ")+": "+Math.ceil(s.missing).toLocaleString()+" short").join(", "));
  if(!parts.length)parts.push("No architectural milestone remains");
  detail.textContent=parts.join(" · ");
  button.append(heading,state,detail);
  button.onclick=()=>(window.ASHFALL_COMMAND40?.inspect?window.ASHFALL_COMMAND40?.inspect(item.key):window.ASHFALL_SELECT_BUILDING?.(item.key));
  list.append(button);
 }
}
function sync(next){data=next;render()}
function select(key){selected=key;render()}
window.ASHFALL_STRATEGY39={sync,select,render};
})();
