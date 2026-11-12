/* ASHFALL 55 — Strategic Development Planner.
 * Read-only comparative analysis of the current authoritative economy snapshot.
 * Never queues construction or predicts future production upgrades. */
(function(){
"use strict";
const $=id=>document.getElementById(id);
const keys=["hq","farm","lumber","salvage","fuel","barracks"];
const conventional=["food","wood","metal","gas"];
let snapshot=null,selected=null,planned=[];
const fmt=n=>Math.max(0,Number(n)||0).toLocaleString(undefined,{maximumFractionDigits:1});
function analyze(key,data){
 const b=data?.buildings?.[key];
 if(!b)return null;
 const level=Number(b.level)||0;
 const max=level>=Number(b.max_level||55);
 const costs={...(b.cost||{}),...(b.rare_cost||{})};
 const gaps=Object.entries(costs).filter(([,amount])=>Number(amount)>0).map(([resource,amount])=>{
  const rare=!conventional.includes(resource);
  const stock=Number((rare?data.rare_materials:data.resources)?.[resource]||0);
  const missing=Math.max(0,Number(amount)-stock);
  const rate=rare?0:Number(data.production_rates?.[resource]?.per_hour||0);
  return {resource,missing,rare,rate,hours:missing<=0?0:rare||rate<=0?Infinity:missing/rate};
 });
 const shortages=gaps.filter(x=>x.missing>0);
 const rareShortages=shortages.filter(x=>x.rare);
 const impossible=shortages.some(x=>!Number.isFinite(x.hours));
 const hours=shortages.length?(impossible?Infinity:Math.max(...shortages.map(x=>x.hours))):0;
 const blockers=[];
 if(max)blockers.push("MAXIMUM LEVEL");
 if(data.queue)blockers.push("CONSTRUCTION SLOT OCCUPIED");
 if(!b.unlocked&&b.unlocked!==undefined)blockers.push("FACILITY LOCKED");

 const eligible=!blockers.length&&!shortages.length;
 return {key,name:b.name||key,level,eligible,max,gaps,shortages,rareShortages,hours,blockers};
}
function estimate(hours){
 if(!Number.isFinite(hours))return "UNAVAILABLE";
 if(hours<=0)return "RESOURCES READY";
 if(hours<1)return "~"+Math.ceil(hours*60)+" MIN";
 if(hours<48)return "~"+hours.toFixed(1)+" H";
 return "~"+(hours/24).toFixed(1)+" DAYS";
}
function ensure(){
 const panel=$("buildpanel");if(!panel)return null;
 let root=$("afPlanner55");if(root)return root;
 root=document.createElement("section");root.id="afPlanner55";root.className="af-planner55";
 root.setAttribute("aria-label","Strategic development comparison");
 const heading=document.createElement("div");heading.className="af-planner-heading55";
 const title=document.createElement("strong");title.textContent="STRATEGIC DEVELOPMENT PLANNER";
 const tag=document.createElement("span");tag.textContent="READ-ONLY INTELLIGENCE";
 heading.append(title,tag);
 const intro=document.createElement("p");
 intro.textContent="Compare the next upgrade of every facility using current stocks, production rates and server-defined requirements.";
 const summary=document.createElement("p");summary.id="afPlannerSummary55";
 const allocation=document.createElement("div");allocation.id="afAllocation56";allocation.className="af-allocation56";
 const allocationHeading=document.createElement("strong");allocationHeading.textContent="RESOURCE ALLOCATION SANDBOX";
 const allocationNote=document.createElement("p");allocationNote.textContent="Reserve next-upgrade costs to compare competing investments. Simulation only; no resources are spent.";
 const allocationState=document.createElement("div");allocationState.id="afAllocationState56";
 const reset=document.createElement("button");reset.type="button";reset.textContent="CLEAR PLAN";reset.onclick=()=>{planned=[];render()};
 reset.className="af-allocation-reset56";
 allocation.append(allocationHeading,allocationNote,allocationState,reset);
 const roadmap=document.createElement("section");roadmap.id="afRoadmap57";roadmap.className="af-roadmap57";
 roadmap.setAttribute("aria-label","Ordered development roadmap");
 const roadTitle=document.createElement("strong");roadTitle.textContent="SETTLEMENT DEVELOPMENT ROADMAP";
 const roadSteps=document.createElement("ol");roadSteps.id="afRoadmapSteps57";
 const roadNote=document.createElement("small");roadNote.textContent="Order is advisory. Each facility shows its current next-upgrade cost only; subsequent upgrade prices are not predicted.";
 roadmap.append(roadTitle,roadSteps,roadNote);
 const list=document.createElement("div");list.id="afPlannerList55";list.className="af-planner-list55";
 const note=document.createElement("small");
 note.textContent="Estimates assume unchanged production and no spending. Rare materials, queues, construction time and server checks can delay upgrades. No automatic construction.";
 root.append(heading,intro,summary,allocation,roadmap,list,note);
 const strategy=$("afStrategy39");
 if(strategy)strategy.insertAdjacentElement("afterend",root);else panel.append(root);
 return root;
}
function render(){
 if(!snapshot||!ensure())return;
 const results=keys.map(key=>analyze(key,snapshot)).filter(Boolean);
 const ready=results.filter(x=>x.eligible).length;
 const feasible=results.filter(x=>!x.max&&Number.isFinite(x.hours)).length;
 $("afPlannerSummary55").textContent=ready+" READY NOW · "+feasible+" WITH ESTIMABLE RESOURCE TIMING · "+results.length+" FACILITIES";
 const available={...snapshot.resources,...snapshot.rare_materials};
 const reserved={};
 for(const key of planned){
  const building=snapshot.buildings?.[key];
  if(!building)continue;
  for(const [resource,cost] of Object.entries({...building.cost,...building.rare_cost})){
   reserved[resource]=(reserved[resource]||0)+Number(cost||0);
  }
 }
 const allocation=$("afAllocationState56");allocation.replaceChildren();
 const allocationText=document.createElement("p");
 allocationText.textContent=planned.length?planned.length+" PLANNED UPGRADES · "+planned.map(key=>snapshot.buildings?.[key]?.name||key).join(" → "):
  "NO UPGRADES RESERVED";
 allocation.append(allocationText);
 for(const resource of Object.keys(reserved).sort()){
  const line=document.createElement("div");line.className="af-allocation-line56";
  const stock=Number(available[resource]||0);
  const deficit=Math.max(0,reserved[resource]-stock);
  line.textContent=resource.toUpperCase()+" · "+fmt(reserved[resource])+" RESERVED / "+fmt(stock)+" OWNED"+
   (deficit?" · SHORT "+fmt(deficit):" · COVERED");
  if(deficit)line.dataset.shortage="true";
  allocation.append(line);
 }
 const roadSteps=$("afRoadmapSteps57");roadSteps.replaceChildren();
 const simulated={...available};
 planned.forEach((key,index)=>{
  const building=snapshot.buildings?.[key];if(!building)return;
  const step=document.createElement("li");step.className="af-roadmap-step57";
  const title=document.createElement("strong");
  title.textContent=(building.name||key)+" · LV "+Number(building.level||0)+" → "+(Number(building.level||0)+1);
  const costs={...building.cost,...building.rare_cost};
  const missing=[];
  for(const [resource,raw] of Object.entries(costs)){
   const need=Math.max(0,Number(raw)||0);
   const stock=Math.max(0,Number(simulated[resource])||0);
   if(need>stock)missing.push(resource.toUpperCase()+" "+fmt(need-stock));
   simulated[resource]=stock-need;
  }
  const detail=document.createElement("small");
  detail.textContent=missing.length?"ADDITIONAL RESOURCES NEEDED · "+missing.join(" · "):"COVERED BY CURRENT UNALLOCATED STOCK";
  const controls=document.createElement("div");controls.className="af-roadmap-controls57";
  for(const [label,delta] of [["MOVE UP",-1],["MOVE DOWN",1]]){
   const action=document.createElement("button");action.type="button";action.textContent=label;
   action.disabled=index+delta<0||index+delta>=planned.length;
   action.onclick=()=>{
    const next=index+delta;
    [planned[index],planned[next]]=[planned[next],planned[index]];
    render();
   };
   controls.append(action);
  }
  step.append(title,detail,controls);roadSteps.append(step);
 });
 if(!planned.length){
  const empty=document.createElement("li");empty.textContent="Choose upgrades below to create a development roadmap.";
  roadSteps.append(empty);
 }
 const list=$("afPlannerList55");list.replaceChildren();
 const ranked=results.sort((a,b)=>Number(b.eligible)-Number(a.eligible)||
  Number(a.max)-Number(b.max)||(Number.isFinite(a.hours)?a.hours:Infinity)-(Number.isFinite(b.hours)?b.hours:Infinity)||keys.indexOf(a.key)-keys.indexOf(b.key));
 for(const item of ranked){
  const button=document.createElement("button");button.type="button";button.className="af-planner-item55";
  button.dataset.afPlanner=item.key;
  button.setAttribute("aria-pressed",String(selected===item.key));
  const head=document.createElement("div");head.className="af-planner-item-head55";
  const title=document.createElement("strong");title.textContent=item.name+" · LV "+item.level;
  const status=document.createElement("span");
  status.textContent=item.max?"MAXIMUM":item.eligible?"READY TO REQUEST":item.blockers.length?"RESTRICTED":"RESOURCE SHORTAGE";
  head.append(title,status);
  const timing=document.createElement("p");
  timing.textContent="RESOURCE TIMING · "+estimate(item.hours);
  const details=document.createElement("small");
  const missing=item.shortages.map(x=>x.resource.toUpperCase()+" "+fmt(x.missing)).join(" · ");
  details.textContent=[missing?"MISSING "+missing:"NO RESOURCE DEFICIT",...item.blockers].join(" · ");
  const reservation=document.createElement("span");
  reservation.className="af-allocation-toggle56";
  reservation.textContent=planned.includes(item.key)?"REMOVE FROM PLAN":"ADD TO PLAN";
  button.append(head,timing,details);
  const planButton=document.createElement("button");planButton.type="button";
  planButton.className="af-allocation-action56";
  planButton.textContent=reservation.textContent;
  planButton.disabled=item.max||(!planned.includes(item.key)&&planned.length>=6);
  planButton.setAttribute("aria-pressed",String(planned.includes(item.key)));
  planButton.onclick=()=>{
   planned=planned.includes(item.key)?planned.filter(k=>k!==item.key):[...planned,item.key];
   render();
  };
  button.onclick=()=>{
   selected=item.key;render();
   if(window.ASHFALL_COMMAND40?.inspect)window.ASHFALL_COMMAND40.inspect(item.key);
   else if(typeof window.ASHFALL_SELECT_BUILDING==="function")window.ASHFALL_SELECT_BUILDING(item.key);
  };
  const entry=document.createElement("div");entry.className="af-planner-entry56";
  entry.append(button,planButton);list.append(entry);
 }
}
function sync(data){snapshot=data;planned=planned.filter(key=>data?.buildings?.[key]&&Number(data.buildings[key].level)<Number(data.buildings[key].max_level||55));render()}
function select(key){selected=key;render()}
window.ASHFALL_PLANNER55={sync,select,analyze};
})();
