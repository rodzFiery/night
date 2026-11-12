/* ASHFALL 40 — Development Command Center.
   Consolidates existing, independently maintained modules into accessible tabs.
   Pure presentation: never changes economy, construction, or upgrade decisions. */
(function(){
"use strict";
const $=id=>document.getElementById(id);
const views=[
 {id:"facilities",label:"FACILITIES",sections:["afRoster36","afUpgradeIntel37"]},
 {id:"architecture",label:"ARCHITECTURE",sections:["afEvolution"]},
 {id:"priorities",label:"PRIORITIES",sections:["afPriorities38"]},
 {id:"strategy",label:"STRATEGY",sections:["afStrategy39"]}
];
let active="facilities";
function ensure(){
 const panel=$("buildpanel");if(!panel)return false;
 let deck=$("afCommandCenter40");
 if(!deck){
  deck=document.createElement("section");deck.id="afCommandCenter40";deck.className="af-command-center40";
  deck.setAttribute("aria-label","Settlement development command center");
  const heading=document.createElement("div");heading.className="af-command-head40";
  const name=document.createElement("strong");name.textContent="DEVELOPMENT COMMAND";
  const hint=document.createElement("span");hint.textContent="SELECT A SYSTEM";
  heading.append(name,hint);
  const tabs=document.createElement("div");tabs.className="af-command-tabs40";tabs.setAttribute("role","tablist");tabs.setAttribute("aria-label","Development systems");
  deck.append(heading,tabs);
  for(const view of views){
   const tab=document.createElement("button");tab.type="button";tab.id="afTab40-"+view.id;
   tab.className="af-command-tab40";tab.setAttribute("role","tab");
   tab.setAttribute("aria-controls","afView40-"+view.id);
   tab.textContent=view.label;
   tab.onclick=()=>activate(view.id,true);
   tab.addEventListener("keydown",event=>{
    if(!["ArrowRight","ArrowLeft","Home","End"].includes(event.key))return;
    event.preventDefault();
    const index=views.findIndex(v=>v.id===view.id);
    const next=event.key==="Home"?0:event.key==="End"?views.length-1:
      (index+(event.key==="ArrowRight"?1:-1)+views.length)%views.length;
    activate(views[next].id,true);
   });
   tabs.append(tab);
   const page=document.createElement("div");page.id="afView40-"+view.id;
   page.className="af-command-view40";page.setAttribute("role","tabpanel");
   page.setAttribute("aria-labelledby",tab.id);page.tabIndex=0;page.hidden=true;
   deck.append(page);
  }
  const title=$("buildtitle");
  if(title)title.insertAdjacentElement("afterend",deck);
  else panel.append(deck);
 }
 for(const view of views){
  const target=$("afView40-"+view.id);
  for(const id of view.sections){
   const node=$(id);
   if(node&&node.parentElement!==target)target.append(node);
  }
 }
 activate(active,false);
 return true;
}
function activate(id,focus){
 if(!views.some(view=>view.id===id))return;
 active=id;
 for(const view of views){
  const selected=view.id===id;
  const tab=$("afTab40-"+view.id),page=$("afView40-"+view.id);
  if(!tab||!page)continue;
  tab.setAttribute("aria-selected",String(selected));
  tab.tabIndex=selected?0:-1;
  page.hidden=!selected;
  if(selected&&focus)tab.focus({preventScroll:true});
 }
}
function sync(){ensure()}
function inspect(key){
  if(typeof window.ASHFALL_SELECT_BUILDING!=="function")return;
  window.ASHFALL_SELECT_BUILDING(key);
  activate("facilities",false);
  const panel=$("buildpanel");
  if(panel&&!panel.hidden)panel.scrollTop=0;
}
window.ASHFALL_COMMAND40={sync,activate,inspect,getActive:()=>active};
})();
