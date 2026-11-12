/* ASHFALL 38 — Settlement Priorities.
 * Read-only, deterministic recommendations from the latest server economy.
 * No inferred future costs, hidden production bonuses, or client-side upgrades.
 */
(function(){
"use strict";
const KEYS=["hq","farm","lumber","salvage","fuel","barracks"];
const TIERS=[5,15,30,50];
const $=id=>document.getElementById(id);
let economy=null,selected=null,filter="all";
function stock(data,key){
 const source=Object.prototype.hasOwnProperty.call(data.resources||{},key)?data.resources:data.rare_materials;
 return Number(source?.[key]||0);
}
function evaluate(data,key){
 const b=data.buildings?.[key];if(!b)return null;
 const level=Number(b.level)||0;
 const max=level>=55;
 const requirements=Object.entries({...b.cost,...b.rare_cost}).filter(([,value])=>Number(value)>0);
 const shortages=requirements.map(([resource,raw])=>({
  resource,need:Number(raw),have:stock(data,resource),
  deficit:Math.max(0,Number(raw)-stock(data,resource))
 })).filter(row=>row.deficit>0);
 const next=TIERS.find(n=>n>level)||null;
 const active=data.queue?.building_key===key;
 const blocked=!!data.queue&&!active;
 const state=max?"max":active?"building":blocked?"waiting":shortages.length?"short":"ready";
 return {key,name:b.name||key,level,next,shortages,state,requirements:requirements.length};
}
function ensure(){
 const panel=$("buildpanel");if(!panel)return null;
 let root=$("afPriorities38");if(root)return root;
 root=document.createElement("section");root.id="afPriorities38";root.className="af-priorities38";
 root.setAttribute("aria-label","Settlement construction priorities");
 const top=document.createElement("div");top.className="af-priorities-head38";
 const title=document.createElement("strong");title.textContent="SETTLEMENT PRIORITIES";
 const count=document.createElement("span");count.id="afPrioritiesSummary38";
 top.append(title,count);
 const controls=document.createElement("div");controls.className="af-priorities-filters38";
 for(const [value,label] of [["all","ALL"],["ready","READY"],["short","SHORTAGES"],["milestone","MILESTONES"]]){
  const button=document.createElement("button");button.type="button";button.dataset.afPriorityFilter=value;
  button.textContent=label;button.onclick=()=>{filter=value;render()};
  controls.append(button);
 }
 const list=document.createElement("div");list.id="afPrioritiesList38";list.className="af-priorities-list38";
 const foot=document.createElement("p");foot.className="af-priorities-foot38";
 foot.textContent="Planning only · Upgrade costs and stock are server-reported. No future costs are projected.";
 root.append(top,controls,list,foot);
 const roster=$("afRoster36");if(roster)roster.insertAdjacentElement("afterend",root);
 else panel.prepend(root);
 return root;
}
function render(){
 if(!economy||!ensure())return;
 const rows=KEYS.map(key=>evaluate(economy,key)).filter(Boolean);
 const ready=rows.filter(r=>r.state==="ready").length;
 const short=rows.filter(r=>r.shortages.length>0).length;
 $("afPrioritiesSummary38").textContent=ready+" READY · "+short+" SHORT";
 for(const button of document.querySelectorAll("[data-af-priority-filter]")){
  button.setAttribute("aria-pressed",String(button.dataset.afPriorityFilter===filter));
 }
 const shown=rows.filter(r=>filter==="all"||filter==="ready"&&r.state==="ready"||filter==="short"&&r.shortages.length>0||filter==="milestone"&&r.next!==null);
 const order={building:0,ready:1,short:2,waiting:3,max:4};
 shown.sort((a,b)=>(order[a.state]??5)-(order[b.state]??5)||
  (a.next===null?Infinity:a.next-a.level)-(b.next===null?Infinity:b.next-b.level)||
  KEYS.indexOf(a.key)-KEYS.indexOf(b.key));
 const list=$("afPrioritiesList38");list.replaceChildren();
 if(!shown.length){const empty=document.createElement("p");empty.className="af-priorities-empty38";empty.textContent="No facilities match this filter.";list.append(empty)}
 for(const row of shown){
  const button=document.createElement("button");button.type="button";button.className="af-priority-card38";
  button.setAttribute("aria-pressed",String(row.key===selected));
  const title=document.createElement("strong");title.textContent=row.name+" · LV "+row.level;
  const state=document.createElement("span");state.className="af-priority-state38";
  state.textContent={ready:"RESOURCES READY",short:"NEEDS RESOURCES",waiting:"CONSTRUCTION SLOT BUSY",building:"CONSTRUCTING",max:"MAX LEVEL"}[row.state];
  const details=document.createElement("small");
  const shortage=row.shortages.map(s=>s.resource.replaceAll("_"," ")+": "+Math.ceil(s.deficit).toLocaleString()+" short").join(" · ");
  const target=row.next===null?"All architectural tiers reached":"Next visual tier LV "+row.next+" ("+(row.next-row.level)+" levels)";
  details.textContent=(shortage?shortage+" · ":"")+target;
  button.append(title,state,details);
  button.onclick=()=>{selected=row.key;render();window.ASHFALL_SELECT_BUILDING?.(row.key)};
  list.append(button);
 }
}
function sync(data){economy=data;render()}
function select(key){selected=key;render()}
window.ASHFALL_PRIORITIES38={sync,select,render};
})();
