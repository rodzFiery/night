/* ASHFALL 37 — Upgrade Intelligence.
   Read-only planning from the server's economy payload; never estimates future costs. */
(function(){
"use strict";
const $=id=>document.getElementById(id);
const milestoneLevels=[5,15,30,50];
let latest=null,active=null;
const fmt=n=>Math.max(0,Math.floor(Number(n)||0)).toLocaleString();
function ensure(){
 const panel=$("buildpanel");if(!panel)return null;
 let root=$("afUpgradeIntel37");if(root)return root;
 root=document.createElement("section");root.id="afUpgradeIntel37";root.className="af-upgrade-intel37";
 root.setAttribute("aria-label","Upgrade intelligence");
 const heading=document.createElement("div");heading.className="af-upgrade-head37";
 const label=document.createElement("strong");label.textContent="UPGRADE INTELLIGENCE";
 const state=document.createElement("span");state.id="afUpgradeState37";
 heading.append(label,state);
 const note=document.createElement("p");note.id="afUpgradeNote37";
 const rows=document.createElement("div");rows.id="afUpgradeResources37";rows.className="af-upgrade-resources37";
 const milestone=document.createElement("p");milestone.id="afUpgradeMilestone37";milestone.className="af-upgrade-milestone37";
 const forecast=document.createElement("div");
 forecast.id="afForecast54";forecast.className="af-forecast54";
 forecast.setAttribute("aria-label","Resource accumulation forecast");
 root.append(heading,note,rows,forecast,milestone);
 const cost=$("buildcost");
 if(cost)cost.insertAdjacentElement("afterend",root);
 else panel.append(root);
 return root;
}
function update(){
 if(!ensure()||!latest||!active)return;
 const building=latest.buildings?.[active];if(!building)return;
 const level=Number(building.level)||0;
 const queue=latest.queue;
 const max=level>=55;
 const costs={...(building.cost||{}),...(building.rare_cost||{})};
 const resources=latest.resources||{};
 const rare=latest.rare_materials||{};
 const list=$("afUpgradeResources37");
 list.replaceChildren();
 let short=0,requirements=0;
 for(const [key,raw] of Object.entries(costs)){
  const need=Number(raw);
  if(!Number.isFinite(need)||need<=0)continue;
  requirements++;
  const owned=Number(Object.prototype.hasOwnProperty.call(resources,key)?resources[key]:rare[key])||0;
  const deficit=Math.max(0,need-owned);
  if(deficit>0)short++;
  const item=document.createElement("div");item.className="af-upgrade-resource37";
  const top=document.createElement("div");top.className="af-upgrade-resource-top37";
  const label=document.createElement("span");label.textContent=key.replaceAll("_"," ").toUpperCase();
  const values=document.createElement("span");values.textContent=fmt(owned)+" / "+fmt(need);
  top.append(label,values);
  const track=document.createElement("div");track.className="af-upgrade-track37";
  const fill=document.createElement("div");fill.style.width=Math.max(0,Math.min(100,need>0?owned/need*100:100))+"%";
  fill.className=deficit?"short":"ready";
  track.append(fill);
  const detail=document.createElement("small");
  detail.textContent=deficit?"SHORT "+fmt(deficit):"SUFFICIENT";
  item.append(top,track,detail);list.append(item);
 }
 const forecast=$("afForecast54");
 if(forecast){
  forecast.replaceChildren();
  const title=document.createElement("strong");title.textContent="RESOURCE READINESS FORECAST";
  forecast.append(title);
  const rates=latest.production_rates;
  const pending=[];
  for(const [resource,cost] of Object.entries(building.cost||{})){
   const deficit=Math.max(0,Number(cost||0)-Number(resources[resource]||0));
   if(deficit<=0)continue;
   const hourly=Number(rates?.[resource]?.per_hour);
   const row=document.createElement("div");row.className="af-forecast-row54";
   const label=document.createElement("span");label.textContent=resource.toUpperCase()+" · "+fmt(deficit)+" needed";
   const value=document.createElement("strong");
   if(!Number.isFinite(hourly)||hourly<=0){
    value.textContent=rates?"NO ACTIVE PRODUCTION":"RATE UNAVAILABLE";
    pending.push(Infinity);
   }else{
    const hours=deficit/hourly;
    pending.push(hours);
    value.textContent=hours<1?"~"+Math.ceil(hours*60)+" MIN":"~"+(hours<48?hours.toFixed(1)+" H":(hours/24).toFixed(1)+" DAYS");
   }
   row.append(label,value);forecast.append(row);
  }
  const summary=document.createElement("p");summary.className="af-forecast-summary54";
  if(max)summary.textContent="Maximum level reached; no further conventional upgrade is available.";
  else if(!pending.length)summary.textContent="Conventional resources ready. Rare materials and upgrade rules are checked separately.";
  else if(pending.some(value=>!Number.isFinite(value)))summary.textContent="At least one missing resource has no reported active production. An automatic readiness time cannot be estimated.";
  else summary.textContent="ESTIMATED RESOURCE READINESS · "+
    (Math.max(...pending)<1?Math.ceil(Math.max(...pending)*60)+" minutes":
     Math.max(...pending)<48?Math.max(...pending).toFixed(1)+" hours":
     (Math.max(...pending)/24).toFixed(1)+" days");
  forecast.append(summary);
  const caveat=document.createElement("small");caveat.className="af-forecast-caveat54";
  caveat.textContent="Planning estimate at current server-reported rates. Assumes no spending, production changes or new bonuses. Construction slot, rare materials and upgrade restrictions may delay building.";
  forecast.append(caveat);
 }
 const state=$("afUpgradeState37"),note=$("afUpgradeNote37");
 if(max){state.textContent="MAXIMUM";note.textContent="This facility has reached the reported maximum level."}
 else if(queue){state.textContent=queue.building_key===active?"CONSTRUCTING":"SLOT OCCUPIED";note.textContent=queue.building_key===active?"This facility has an active construction order.":"Construction is occupied by "+String(queue.building_key).replaceAll("_"," ")+". You can plan the next upgrade."}
 else if(short){state.textContent="RESOURCES NEEDED";note.textContent=short+" resource "+(short===1?"type is":"types are")+" below the next upgrade requirement."}
 else{state.textContent="RESOURCES READY";note.textContent=requirements?"All listed resources are sufficient for the next upgrade. Server validation is still required.":"No resource requirements were supplied for this upgrade. Server validation is required."}
 const next=milestoneLevels.find(n=>n>level);
 $("afUpgradeMilestone37").textContent=next?"ARCHITECTURAL TARGET · LEVEL "+next+" · "+(next-level)+" "+(next-level===1?"level":"levels")+" away. Future upgrade costs are not projected.":"All four architectural tiers reached. Further progression depends on the server's level cap.";
}
function sync(data){latest=data;update()}
function select(key){active=key;update()}
window.ASHFALL_UPGRADE_INTEL37={sync,select,update};
})();
