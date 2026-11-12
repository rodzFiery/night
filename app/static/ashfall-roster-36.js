/* ASHFALL 36 — Settlement Development Roster.
   All levels, costs, and queue states come from the economy response.
   Navigation is read-only; upgrades remain handled by the existing server API. */
(function(){
"use strict";
const keys=["hq","farm","lumber","salvage","fuel","barracks"];
const names={hq:"Command Center",farm:"Farm",lumber:"Lumber Yard",salvage:"Salvage Station",fuel:"Fuel Collector",barracks:"Barracks"};
const $=id=>document.getElementById(id);
let latest=null,selected=null;
function make(){
 const panel=$("buildpanel");
 if(!panel)return null;
 let root=$("afRoster36");
 if(root)return root;
 root=document.createElement("section");
 root.id="afRoster36";root.className="af-roster36";
 root.setAttribute("aria-label","Settlement facility navigator");
 const heading=document.createElement("div");
 heading.className="af-roster-heading36";
 const title=document.createElement("strong");title.textContent="SETTLEMENT FACILITIES";
 const count=document.createElement("span");count.id="afRosterCount36";
 heading.append(title,count);
 const list=document.createElement("div");list.id="afRosterList36";list.className="af-roster-list36";
 root.append(heading,list);
 const eyebrow=panel.querySelector(".eyebrow");
 if(eyebrow)eyebrow.insertAdjacentElement("afterend",root);
 else panel.prepend(root);
 return root;
}
function affordability(building,resources,materials){
 const requirements={...(building.cost||{}),...(building.rare_cost||{})};
 const missing=Object.entries(requirements).filter(([key,amount])=>{
  const stock=Object.prototype.hasOwnProperty.call(resources,key)?resources[key]:materials[key];
  return Number(stock||0)<Number(amount||0);
 });
 return missing;
}
function render(){
 if(!make()||!latest)return;
 const list=$("afRosterList36");
 const queue=latest.queue?.building_key;
 const resources=latest.resources||{};
 const materials=latest.rare_materials||{};
 list.replaceChildren();
 let ready=0;
 for(const key of keys){
  const building=latest.buildings?.[key];
  if(!building)continue;
  const level=Number(building.level)||0;
  const max=level>=55;
  const missing=affordability(building,resources,materials);
  const active=queue===key;
  const canStart=!queue&&!max&&missing.length===0;
  if(canStart)ready++;
  const button=document.createElement("button");
  button.type="button";button.className="af-roster-item36";
  button.setAttribute("aria-pressed",String(selected===key));
  button.setAttribute("aria-label",(building.name||names[key])+", level "+level+", inspect facility");
  const left=document.createElement("span");left.className="af-roster-name36";
  left.textContent=building.name||names[key];
  const right=document.createElement("span");right.className="af-roster-status36";
  right.textContent=active?"BUILDING":max?"MAX":queue?"QUEUED SLOT":missing.length?"NEEDS RESOURCES":"READY";
  right.dataset.state=active?"active":canStart?"ready":"neutral";
  const lvl=document.createElement("small");lvl.textContent="LV "+level;
  button.append(left,lvl,right);
  button.onclick=()=>{selected=key;render();if(typeof window.ASHFALL_SELECT_BUILDING==="function")window.ASHFALL_SELECT_BUILDING(key);};
  list.append(button);
 }
 $("afRosterCount36").textContent=queue?"1 ACTIVE":ready+" READY";
}
function sync(data){latest=data;render()}
function select(key){selected=key;render()}
window.ASHFALL_ROSTER36={sync,select,render};
})();
