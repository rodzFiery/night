/* ASHFALL 55 — Strategic Development Planner.
 * Read-only comparative analysis of the current authoritative economy snapshot.
 * Never queues construction or predicts future production upgrades. */
(function(){
"use strict";
const $=id=>document.getElementById(id);
const keys=["hq","farm","lumber","salvage","fuel","barracks"];
const conventional=["food","wood","metal","gas"];
let snapshot=null,selected=null;
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
 const hq=Number(data.buildings?.hq?.level||0);
 const blockers=[];
 if(max)blockers.push("MAXIMUM LEVEL");
 if(data.queue)blockers.push("CONSTRUCTION SLOT OCCUPIED");
 if(!b.unlocked&&b.unlocked!==undefined)blockers.push("FACILITY LOCKED");
 if(key!=="hq"&&level+1>hq)blockers.push("COMMAND CENTER LEVEL REQUIRED");
 if(level>=30&&hq<30)blockers.push("CRYSTAL AGE REQUIRES HQ 30");
 if(key==="hq"&&level>=2&&["farm","lumber","salvage","fuel"].some(k=>Number(data.buildings?.[k]?.level||0)<level-1))
  blockers.push("PRODUCTION FACILITIES REQUIRE DEVELOPMENT");
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
 const list=document.createElement("div");list.id="afPlannerList55";list.className="af-planner-list55";
 const note=document.createElement("small");
 note.textContent="Estimates assume unchanged production and no spending. Rare materials, queues, construction time and server checks can delay upgrades. No automatic construction.";
 root.append(heading,intro,summary,list,note);
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
 const list=$("afPlannerList55");list.replaceChildren();
 const ranked=results.sort((a,b)=>Number(b.eligible)-Number(a.eligible)||
  Number(a.max)-Number(b.max)||a.hours-b.hours||keys.indexOf(a.key)-keys.indexOf(b.key));
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
  button.append(head,timing,details);
  button.onclick=()=>{
   selected=item.key;render();
   if(typeof window.ASHFALL_SELECT_BUILDING==="function")window.ASHFALL_SELECT_BUILDING(item.key);
   window.ASHFALL_COMMAND40?.open?.("facilities");
  };
  list.append(button);
 }
}
function sync(data){snapshot=data;render()}
function select(key){selected=key;render()}
window.ASHFALL_PLANNER55={sync,select,analyze};
})();
