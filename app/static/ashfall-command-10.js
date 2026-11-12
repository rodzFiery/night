/* ASHFALL 9.1 — Accessible interactive command console, existing game actions preserved. */
(()=>{"use strict";
const NS="http://www.w3.org/2000/svg";
const icons={
grid:'<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
eye:'<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>',
home:'<path d="m3 10 9-7 9 7v10H3z"/><path d="M9 20v-7h6v7"/>',
map:'<path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3z"/><path d="M9 3v15M15 6v15"/>',
flask:'<path d="M9 3h6m-5 0v7L5 19a2 2 0 0 0 2 3h10a2 2 0 0 0 2-3l-5-9V3"/><path d="M8 16h8"/>',
users:'<circle cx="9" cy="8" r="3"/><path d="M3 21v-2a6 6 0 0 1 12 0v2M17 5a3 3 0 0 1 0 6m1 4a5 5 0 0 1 3 5"/>',
shield:'<path d="M12 2 3 6v6c0 5 4 8 9 10 5-2 9-5 9-10V6z"/><path d="m8 12 3 3 5-6"/>',
compass:'<circle cx="12" cy="12" r="9"/><path d="m15 9-2 5-5 2 2-5z"/>',
swords:'<path d="M4 4 20 20M20 4 4 20M4 4l5 1-4 4-1-5M20 4l-5 1 4 4 1-5"/>',
star:'<path d="m12 2 2.4 7.6L22 12l-7.6 2.4L12 22l-2.4-7.6L2 12l7.6-2.4z"/>',
flag:'<path d="M5 22V3m0 1c5-4 9 4 15 0v11c-6 4-10-4-15 0"/>',
chest:'<rect x="3" y="8" width="18" height="13" rx="2"/><path d="M3 12h18M9 8V5a3 3 0 0 1 6 0v3M12 12v4"/>',
target:'<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
strategy:'<path d="M4 4h7v7H4zM13 13h7v7h-7zM7 11v6h6"/>'
};
const groups=[
{label:"WORLD",entries:[["Settlement","Manage your Haven and buildings","home","settlement"],["Wilderness","Explore the living world","map","wilderness"],["Recenter","Return to your Haven","target","center"],["Objectives","Track your next milestone","flag","missionToggle"]]},
{label:"DEVELOPMENT",entries:[["Research","Technology and progression","flask","researchButton"],["Heroes","Your commanders and roster","users","heroesButton"],["Hero Command","Open full hero collection","users","/ashfall/heroes"],["Grand Arsenal","Craft, inspect and enhance equipment","chest","/ashfall/arsenal"],["Crystal Frontier","Expeditions, research, refining and Crystal Age legacy","star","/ashfall/crystal-frontier"]]},
{label:"OPERATIONS",entries:[["Military","Troops and training","shield","militaryButton"],["Expeditions","Gather resources beyond the Haven","compass","expeditionButton"],["Encounters","Tactical encounter command","swords","combatButton"],["Events","Discoveries and activities","star","eventsButton"],["Alliances","Diplomacy and cooperation","flag","alliancesButton"],["Strategic Command","Review Haven operations","strategy","opsToggle"]]}
];
const make=(tag,cls,text)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e};
function svg(name){const s=document.createElementNS(NS,"svg");s.setAttribute("viewBox","0 0 24 24");s.setAttribute("aria-hidden","true");s.innerHTML=icons[name]||icons.star;return s}
function init(){
 if(!document.getElementById("world")||document.getElementById("af10-tools"))return;
 let active=0,lastFocus=null;
 const tools=make("div","af10-tools");tools.id="af10-tools";tools.setAttribute("role","group");tools.setAttribute("aria-label","World view controls");
 const consoleBtn=make("button","af10-tool");consoleBtn.type="button";consoleBtn.append(svg("grid"),make("span","", "COMMAND CENTER"));consoleBtn.title="Open command center (press G)";
 const immersiveBtn=make("button","af10-tool");immersiveBtn.type="button";immersiveBtn.append(svg("eye"),make("span","",""));immersiveBtn.querySelector("span").textContent="IMMERSIVE VIEW";immersiveBtn.title="Toggle immersive view (press H)";
 immersiveBtn.setAttribute("aria-pressed","false");
 tools.append(consoleBtn,immersiveBtn);document.body.append(tools);
 const overlay=make("div","af10-modal");overlay.hidden=true;overlay.setAttribute("role","presentation");
 const panel=make("section","af10-console");panel.setAttribute("role","dialog");panel.setAttribute("aria-modal","true");panel.setAttribute("aria-label","ASHFALL command center");
 const head=make("header","af10-head");const heading=make("div");heading.append(make("div","af10-kicker","ASHFALL / STRATEGIC INTERFACE"),make("h2","","COMMAND CENTER"));
 const close=make("button","af10-close","×");close.type="button";close.setAttribute("aria-label","Close command center");head.append(heading,close);
 const intro=make("p","af10-intro","Choose a division to access existing ASHFALL systems. Every command uses the game's current navigation and mechanics.");
 const tabs=make("div","af10-tabs");tabs.setAttribute("role","tablist");tabs.setAttribute("aria-label","Command divisions");
 const content=make("div","af10-content");const footer=make("div","af10-footer","G · COMMAND CENTER     H · IMMERSIVE VIEW     ESC · CLOSE");
 panel.append(head,intro,tabs,content,footer);overlay.append(panel);document.body.append(overlay);
 function closeModal(){overlay.hidden=true;if(lastFocus&&lastFocus.isConnected)lastFocus.focus()}
 function openModal(){lastFocus=document.activeElement;overlay.hidden=false;render();close.focus()}
 function dispatch(dest){closeModal();if(dest.startsWith("/")){window.location.assign(dest);return}const btn=document.getElementById(dest);if(btn)btn.click()}
 function render(){
  tabs.replaceChildren();content.replaceChildren();
  groups.forEach((g,i)=>{const t=make("button","af10-tab",g.label);t.type="button";t.setAttribute("role","tab");t.setAttribute("aria-selected",String(i===active));t.tabIndex=i===active?0:-1;t.onclick=()=>{active=i;render();tabs.children[i].focus()};tabs.append(t)});
  const grid=make("div","af10-grid");
  for(const [name,description,ico,dest] of groups[active].entries){
   const b=make("button","af10-action");b.type="button";b.append(svg(ico),make("strong","",name.toUpperCase()),make("small","",description));b.onclick=()=>dispatch(dest);grid.append(b)
  }content.append(grid)
 }
 consoleBtn.onclick=openModal;close.onclick=closeModal;overlay.addEventListener("click",e=>{if(e.target===overlay)closeModal()});
 immersiveBtn.onclick=()=>{const on=document.body.classList.toggle("af10-immersive");immersiveBtn.setAttribute("aria-pressed",String(on));immersiveBtn.title=on?"Exit immersive view (press H)":"Toggle immersive view (press H)"};
 document.addEventListener("keydown",e=>{
  const tag=(e.target&&e.target.tagName||"").toLowerCase();if(["input","textarea","select"].includes(tag)||e.target?.isContentEditable)return;
  if(e.key==="Escape"&&!overlay.hidden){e.preventDefault();closeModal();return}
  if(e.altKey||e.ctrlKey||e.metaKey||e.repeat)return;
  if(e.key.toLowerCase()==="g"&&overlay.hidden){e.preventDefault();openModal()}
  else if(e.key.toLowerCase()==="h"&&overlay.hidden){e.preventDefault();immersiveBtn.click()}
  else if(!overlay.hidden&&["ArrowLeft","ArrowRight"].includes(e.key)){e.preventDefault();active=(active+(e.key==="ArrowRight"?1:groups.length-1))%groups.length;render();tabs.children[active].focus()}
  else if(!overlay.hidden&&e.key==="Tab"){
   const focusable=[...panel.querySelectorAll('button:not([disabled]):not([tabindex="-1"])')];const first=focusable[0],last=focusable[focusable.length-1];
   if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()}
  }
 });
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init,{once:true});else init();
})();