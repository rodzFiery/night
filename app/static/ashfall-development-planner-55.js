/* ASHFALL 55 — Strategic Development Planner.
 * Read-only comparative analysis of the current authoritative economy snapshot.
 * Never queues construction or predicts future production upgrades. */
(function(){
"use strict";
const $=id=>document.getElementById(id);
const keys=["hq","farm","lumber","salvage","fuel","barracks"];
const conventional=["food","wood","metal","gas"];
let snapshot=null,selected=null,planned=[],scenarioResource="wood",scenarioBoost=10;
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
  const rawRate=data.production_rates?.[resource]?.per_hour;
  const rate=rare?0:Number(rawRate);
  return {resource,missing,rare,rate,hours:missing<=0?0:rare||rawRate==null||rawRate===""||!Number.isFinite(rate)||rate<=0?Infinity:missing/rate};
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
function roadmapAudit(data,order){
 const remaining={...data.resources,...data.rare_materials};
 const steps=[];
 const totals={};
 for(const key of order){
  const building=data.buildings?.[key];
  if(!building)continue;
  const costs={...building.cost,...building.rare_cost};
  const shortages={};
  for(const [resource,raw] of Object.entries(costs)){
   const amount=Math.max(0,Number(raw)||0);
   totals[resource]=(totals[resource]||0)+amount;
   const balance=Number(remaining[resource])||0;
   const shortage=Math.max(0,amount-balance);
   if(shortage>0)shortages[resource]=shortage;
   remaining[resource]=balance-amount;
  }
  steps.push({key,shortages});
 }
 const bottlenecks=Object.entries(totals).map(([resource,required])=>{
  const stock=Number((conventional.includes(resource)?data.resources:data.rare_materials)?.[resource]||0);
  const deficit=Math.max(0,required-stock);
  const rare=!conventional.includes(resource);
  const rawRate=data.production_rates?.[resource]?.per_hour;
  const rate=Number(rawRate);
  const known=!rare&&rawRate!==undefined&&rawRate!==null&&rawRate!==""&&Number.isFinite(rate)&&rate>=0;
  const hours=deficit===0?0:known&&rate>0?deficit/rate:Infinity;
  return {resource,required,stock,deficit,rare,rate:known?rate:0,hours,known};
 }).sort((a,b)=>{
  const left=a.deficit>0?(Number.isFinite(a.hours)?a.hours:Infinity):-1;
  const right=b.deficit>0?(Number.isFinite(b.hours)?b.hours:Infinity):-1;
  if(left===right)return a.resource.localeCompare(b.resource);
  return right>left?1:-1;
 });
 return {steps,bottlenecks,totals};
}
/* ASHFALL 62 — hypothetical current-rate scenarios, never mutate the snapshot. */
function scenarioComparison(data,order,resource,boostPercent){
 const audit=roadmapAudit(data,order);
 const percent=Math.max(0,Math.min(100,Number(boostPercent)||0));
 const rows=audit.bottlenecks.map(item=>{
  const boosted=item.resource===resource&&!item.rare&&item.known&&item.rate>0;
  const scenarioRate=boosted?item.rate*(1+percent/100):item.rate;
  const scenarioHours=item.deficit===0?0:item.rare||!item.known||scenarioRate<=0?Infinity:item.deficit/scenarioRate;
  return {...item,scenarioRate,scenarioHours,hoursSaved:
   Number.isFinite(item.hours)&&Number.isFinite(scenarioHours)?Math.max(0,item.hours-scenarioHours):0};
 });
 const longest=field=>rows.reduce((maximum,item)=>item.deficit>0?Math.max(maximum,item[field]):maximum,0);
 return {rows,baselineHours:longest("hours"),scenarioHours:longest("scenarioHours"),resource,percent};
}
/* ASHFALL 63 — fair comparisons: identical boost for each candidate resource. */
function rankScenarios(data,order,boostPercent){
 const percent=Math.max(0,Math.min(100,Number(boostPercent)||0));
 const options=conventional.map(resource=>{
  const result=scenarioComparison(data,order,resource,percent);
  const gain=Number.isFinite(result.baselineHours)&&Number.isFinite(result.scenarioHours)?
   Math.max(0,result.baselineHours-result.scenarioHours):0;
  const focus=result.rows.find(row=>row.resource===resource);
  return {resource,percent,baselineHours:result.baselineHours,
   scenarioHours:result.scenarioHours,gain,focus,
   blocked:!Number.isFinite(result.scenarioHours)};
 });
 options.sort((a,b)=>b.gain-a.gain||
  (Number.isFinite(a.scenarioHours)?a.scenarioHours:Infinity)-(Number.isFinite(b.scenarioHours)?b.scenarioHours:Infinity)||
  conventional.indexOf(a.resource)-conventional.indexOf(b.resource));
 return options;
}
/* ASHFALL 64 — milestone intelligence based only on server-reported levels. */
const milestoneTiers=[5,15,30,50];
function developmentMilestones(data,order){
 const facilities=keys.filter(key=>data?.buildings?.[key]);
 const levels=facilities.map(key=>({key,name:data.buildings[key].name||key,
  level:Math.max(0,Number(data.buildings[key].level)||0)}));
 const lowest=levels.length?Math.min(...levels.map(item=>item.level)):0;
 const tiers=milestoneTiers.map(target=>{
  const reached=levels.filter(item=>item.level>=target);
  const pending=levels.filter(item=>item.level<target);
  return {target,reached:reached.length,total:levels.length,
   complete:levels.length>0&&pending.length===0,pending,
   percent:levels.length?Math.round(reached.length/levels.length*100):0};
 });
 const next=tiers.find(tier=>!tier.complete)||null;
 const priority=next?[...next.pending].sort((a,b)=>a.level-b.level||
  facilities.indexOf(a.key)-facilities.indexOf(b.key))[0]:null;
 const plannedTowardNext=next?order.filter(key=>next.pending.some(item=>item.key===key)): [ ];
 return {levels,lowest,tiers,next,priority,plannedTowardNext};
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
 const bottlenecks=document.createElement("section");bottlenecks.id="afBottlenecks58";bottlenecks.className="af-bottlenecks58";
 bottlenecks.setAttribute("aria-label","Strategic resource bottlenecks");
 const bottleneckTitle=document.createElement("strong");bottleneckTitle.textContent="STRATEGIC BOTTLENECK INTELLIGENCE";
 const bottleneckRows=document.createElement("div");bottleneckRows.id="afBottleneckRows58";
 const bottleneckNote=document.createElement("small");
 bottleneckNote.textContent="Current-rate estimates only. This analysis does not model spending, production changes, queues, future building costs or rare-material acquisition.";
 bottlenecks.append(bottleneckTitle,bottleneckRows,bottleneckNote);
 const scenarios=document.createElement("section");scenarios.id="afScenarios62";scenarios.className="af-scenarios62";
 scenarios.setAttribute("aria-label","Hypothetical production scenario comparison");
 const scenarioTitle=document.createElement("strong");scenarioTitle.textContent="STRATEGIC SCENARIO LAB";
 const scenarioIntro=document.createElement("p");scenarioIntro.textContent="Explore hypothetical production changes without modifying live economy rates or spending resources.";
 const controls=document.createElement("div");controls.className="af-scenario-controls62";
 const resourceLabel=document.createElement("label");resourceLabel.textContent="RESOURCE";
 const resourceSelect=document.createElement("select");resourceSelect.id="afScenarioResource62";
 for(const resource of conventional){
  const option=document.createElement("option");option.value=resource;option.textContent=resource.toUpperCase();
  resourceSelect.append(option);
 }
 resourceSelect.value=scenarioResource;
 resourceSelect.onchange=()=>{scenarioResource=resourceSelect.value;render()};
 resourceLabel.append(resourceSelect);
 const boostLabel=document.createElement("label");boostLabel.textContent="HYPOTHETICAL PRODUCTION BOOST";
 const boostSelect=document.createElement("select");boostSelect.id="afScenarioBoost62";
 for(const amount of [0,5,10,20,50,100]){
  const option=document.createElement("option");option.value=String(amount);option.textContent="+"+amount+"%";
  boostSelect.append(option);
 }
 boostSelect.value=String(scenarioBoost);
 boostSelect.onchange=()=>{scenarioBoost=Number(boostSelect.value);render()};
 boostLabel.append(boostSelect);
 controls.append(resourceLabel,boostLabel);
 const scenarioResults=document.createElement("div");scenarioResults.id="afScenarioResults62";
 const scenarioDisclaimer=document.createElement("small");
 scenarioDisclaimer.textContent="Illustrative comparison only: assumes fixed current rates and unchanged stocks. Does not model construction, research costs, cooldowns or actual future production.";
 scenarios.append(scenarioTitle,scenarioIntro,controls,scenarioResults,scenarioDisclaimer);
 const comparison=document.createElement("section");comparison.id="afCompare63";comparison.className="af-compare63";
 comparison.setAttribute("aria-label","Production scenario comparison");
 const compareTitle=document.createElement("strong");compareTitle.textContent="ECONOMIC STRATEGY COMPARISON";
 const compareIntro=document.createElement("p");compareIntro.textContent="Compare an equal hypothetical boost across all four conventional resources. The strongest result is ranked first.";
 const compareRows=document.createElement("div");compareRows.id="afCompareRows63";
 const compareNote=document.createElement("small");compareNote.textContent="Ranking uses the longest outstanding resource wait. Ties follow resource order. Unavailable or rare-material-blocked forecasts are not presented as improvements.";
 comparison.append(compareTitle,compareIntro,compareRows,compareNote);
 const milestones=document.createElement("section");milestones.id="afMilestones64";milestones.className="af-milestones64";
 milestones.setAttribute("aria-label","Settlement development milestones");
 const milestoneTitle=document.createElement("strong");milestoneTitle.textContent="SETTLEMENT DEVELOPMENT MILESTONES";
 const milestoneIntro=document.createElement("p");milestoneIntro.textContent="Track architectural level thresholds across all six facilities. Progress comes from server-reported levels, never hypothetical upgrades.";
 const milestoneSummary=document.createElement("p");milestoneSummary.id="afMilestoneSummary64";
 const milestoneRows=document.createElement("div");milestoneRows.id="afMilestoneRows64";
 const milestoneNote=document.createElement("small");milestoneNote.textContent="Legacy achievements are awarded by the server only. This panel does not grant resources, unlock eras or alter progression.";
 milestones.append(milestoneTitle,milestoneIntro,milestoneSummary,milestoneRows,milestoneNote);
 const list=document.createElement("div");list.id="afPlannerList55";list.className="af-planner-list55";
 const note=document.createElement("small");
 note.textContent="Estimates assume unchanged production and no spending. Rare materials, queues, construction time and server checks can delay upgrades. No automatic construction.";
 root.append(heading,intro,summary,allocation,roadmap,bottlenecks,scenarios,comparison,milestones,list,note);
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
 const audit=roadmapAudit(snapshot,planned);
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
 const bottleneckRows=$("afBottleneckRows58");bottleneckRows.replaceChildren();
 const intelligence=audit.bottlenecks;
 if(!intelligence.length){
  const empty=document.createElement("p");empty.textContent="Add upgrades to reveal resource bottlenecks across your roadmap.";
  bottleneckRows.append(empty);
 }
 for(const item of intelligence){
  const row=document.createElement("div");row.className="af-bottleneck-row58";
  row.dataset.resource=item.resource;
  if(item.deficit>0)row.dataset.shortage="true";
  const head=document.createElement("div");head.className="af-bottleneck-head58";
  const name=document.createElement("strong");name.textContent=item.resource.replaceAll("_"," ").toUpperCase();
  const status=document.createElement("span");
  status.textContent=!item.deficit?"COVERED":item.rare?"RARE MATERIAL":!item.known?"RATE UNKNOWN":item.rate<=0?"NO PRODUCTION":"BOTTLENECK";
  head.append(name,status);
  const track=document.createElement("div");track.className="af-bottleneck-track58";
  track.setAttribute("role","progressbar");track.setAttribute("aria-label",name.textContent+" roadmap coverage");
  const coverage=Math.max(0,Math.min(100,item.required>0?item.stock/item.required*100:100));
  track.setAttribute("aria-valuemin","0");track.setAttribute("aria-valuemax","100");
  track.setAttribute("aria-valuenow",String(Math.round(coverage)));
  const fill=document.createElement("div");fill.style.width=coverage+"%";track.append(fill);
  const detail=document.createElement("small");
  detail.textContent=fmt(item.stock)+" / "+fmt(item.required)+" · "+
   (item.deficit?"SHORT "+fmt(item.deficit)+" · "+(item.rare?"ACQUISITION REQUIRED":!item.known?"RATE UNAVAILABLE":item.rate<=0?"PRODUCTION REQUIRED":estimate(item.hours)):"RESOURCES AVAILABLE");
  row.append(head,track,detail);bottleneckRows.append(row);
 }
 const blocked=intelligence.filter(item=>item.deficit>0&&!Number.isFinite(item.hours));
 const slowest=intelligence.find(item=>item.deficit>0&&Number.isFinite(item.hours));
 const verdict=document.createElement("p");verdict.id="afBottleneckVerdict58";
 verdict.textContent=!planned.length?"NO ACTIVE ROADMAP":
  blocked.length?"ROADMAP BLOCKED · "+blocked.map(item=>item.resource.toUpperCase()).join(", "):
  slowest?"PRIMARY BOTTLENECK · "+slowest.resource.toUpperCase()+" · "+estimate(slowest.hours):
  "ALL PLANNED RESOURCE COSTS COVERED";
 bottleneckRows.prepend(verdict);
 const comparison=scenarioComparison(snapshot,planned,scenarioResource,scenarioBoost);
 const scenarioResults=$("afScenarioResults62");scenarioResults.replaceChildren();
 const scenarioSummary=document.createElement("p");scenarioSummary.className="af-scenario-summary62";
 scenarioSummary.textContent=!planned.length?"SELECT UPGRADES TO COMPARE SCENARIOS":
  "BASELINE · "+estimate(comparison.baselineHours)+"   |   HYPOTHETICAL · "+estimate(comparison.scenarioHours);
 scenarioResults.append(scenarioSummary);
 const focus=comparison.rows.find(row=>row.resource===scenarioResource);
 if(focus&&planned.length){
  const detail=document.createElement("p");
  detail.textContent=scenarioResource.toUpperCase()+" · "+
   (focus.deficit===0?"NO DEFICIT":
    "BASELINE "+estimate(focus.hours)+" · SCENARIO "+estimate(focus.scenarioHours)+
    " · POTENTIAL SAVING "+(focus.hoursSaved>0?estimate(focus.hoursSaved):"NONE"));
  scenarioResults.append(detail);
 }
 const rankedScenarios=rankScenarios(snapshot,planned,scenarioBoost);
 const compareRows=$("afCompareRows63");compareRows.replaceChildren();
 if(!planned.length){
  const empty=document.createElement("p");empty.textContent="Add roadmap upgrades to compare production priorities.";
  compareRows.append(empty);
 }
 for(const [index,item] of rankedScenarios.entries()){
  if(!planned.length)break;
  const row=document.createElement("div");row.className="af-compare-row63";
  const head=document.createElement("div");head.className="af-compare-head63";
  const name=document.createElement("strong");name.textContent=(index+1)+". "+item.resource.toUpperCase();
  const result=document.createElement("span");
  result.textContent=item.gain>0?"SAVE "+estimate(item.gain):item.blocked?"BLOCKED / UNKNOWN":"NO GLOBAL SAVING";
  head.append(name,result);
  const detail=document.createElement("small");
  detail.textContent="+"+item.percent+"% HYPOTHETICAL · "+estimate(item.baselineHours)+" → "+estimate(item.scenarioHours);
  const select=document.createElement("button");select.type="button";select.textContent="INSPECT SCENARIO";
  select.setAttribute("aria-label","Inspect "+item.resource+" scenario");
  select.onclick=()=>{
   scenarioResource=item.resource;
   const dropdown=$("afScenarioResource62");if(dropdown)dropdown.value=item.resource;
   render();
  };
  row.append(head,detail,select);compareRows.append(row);
 }
 const milestoneState=developmentMilestones(snapshot,planned);
 const milestoneSummary=$("afMilestoneSummary64");
 milestoneSummary.textContent=milestoneState.next?
  "NEXT OBJECTIVE · ALL FACILITIES LEVEL "+milestoneState.next.target+
  " · "+milestoneState.next.reached+"/"+milestoneState.next.total+" REACHED"+
  (milestoneState.priority?" · LOWEST: "+milestoneState.priority.name.toUpperCase()+" LV "+milestoneState.priority.level:""):
  "ALL TRACKED DEVELOPMENT THRESHOLDS REACHED";
 const earnedTiers=new Map((snapshot.settlement_achievements?.tiers||[]).map(item=>[Number(item.level),item]));
 const milestoneRows=$("afMilestoneRows64");milestoneRows.replaceChildren();
 for(const tier of milestoneState.tiers){
  const row=document.createElement("div");row.className="af-milestone-row64";
  const head=document.createElement("div");head.className="af-milestone-head64";
  const title=document.createElement("strong");title.textContent="LEVEL "+tier.target+" · SETTLEMENT-WIDE";
  const status=document.createElement("span");
  const earned=earnedTiers.get(tier.target);
  status.textContent=earned?.earned?"LEGACY EARNED":tier.complete?"THRESHOLD REACHED · AWAITING SERVER CONFIRMATION":tier.reached+"/"+tier.total+" FACILITIES";
  head.append(title,status);
  const track=document.createElement("div");track.className="af-milestone-track64";
  track.setAttribute("role","progressbar");track.setAttribute("aria-label","Level "+tier.target+" facility coverage");
  track.setAttribute("aria-valuemin","0");track.setAttribute("aria-valuemax","100");
  track.setAttribute("aria-valuenow",String(tier.percent));
  const fill=document.createElement("div");fill.style.width=tier.percent+"%";track.append(fill);
  const detail=document.createElement("small");
  detail.textContent=earned?.earned?"PERMANENT HAVEN ACHIEVEMENT RECORDED":tier.complete?"ALL FACILITIES REACHED":
   tier.pending.map(item=>item.name.toUpperCase()+" LV "+item.level).join(" · ");
  row.append(head,track,detail);milestoneRows.append(row);
 }
 const roadSteps=$("afRoadmapSteps57");roadSteps.replaceChildren();
 planned.forEach((key,index)=>{
  const building=snapshot.buildings?.[key];if(!building)return;
  const step=document.createElement("li");step.className="af-roadmap-step57";
  const title=document.createElement("strong");
  title.textContent=(building.name||key)+" · LV "+Number(building.level||0)+" → "+(Number(building.level||0)+1);
  const missing=Object.entries(audit.steps[index]?.shortages||{})
   .map(([resource,amount])=>resource.toUpperCase()+" "+fmt(amount));
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
window.ASHFALL_PLANNER55={sync,select,analyze,roadmapAudit,scenarioComparison,rankScenarios,developmentMilestones};
})();
