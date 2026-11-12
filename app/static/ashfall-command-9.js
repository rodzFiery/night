/* ASHFALL 9.0 — non-destructive navigation enhancement.
   Adds accessible SVG icons and working quick links; leaves existing handlers intact. */
(()=>{"use strict";
const shapes={
 home:'<path d="m3 10 9-7 9 7v10H3z"/><path d="M9 20v-7h6v7"/>',
 map:'<path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3z"/><path d="M9 3v15M15 6v15"/>',
 flask:'<path d="M9 3h6m-5 0v7L5 19a2 2 0 0 0 2 3h10a2 2 0 0 0 2-3l-5-9V3"/><path d="M8 16h8"/>',
 users:'<circle cx="9" cy="8" r="3"/><path d="M3 21v-2a6 6 0 0 1 12 0v2M17 5a3 3 0 0 1 0 6m1 4a5 5 0 0 1 3 5"/>',
 shield:'<path d="M12 2 3 6v6c0 5 4 8 9 10 5-2 9-5 9-10V6z"/><path d="m8 12 3 3 5-6"/>',
 compass:'<circle cx="12" cy="12" r="9"/><path d="m15 9-2 5-5 2 2-5z"/>',
 swords:'<path d="M4 4 20 20M20 4 4 20M4 4l5 1-4 4-1-5M20 4l-5 1 4 4 1-5M3 21l5-5M21 21l-5-5"/>',
 sparkle:'<path d="m12 2 2.4 7.6L22 12l-7.6 2.4L12 22l-2.4-7.6L2 12l7.6-2.4z"/>',
 flag:'<path d="M5 22V3m0 1c5-4 9 4 15 0v11c-6 4-10-4-15 0"/>',
 target:'<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
 search:'<circle cx="11" cy="11" r="7"/><path d="m16 16 5 5"/>',
 strategy:'<path d="M4 4h7v7H4zM13 13h7v7h-7zM7 11v6h6"/>',
 chest:'<rect x="3" y="8" width="18" height="13" rx="2"/><path d="M3 12h18M9 8V5a3 3 0 0 1 6 0v3M12 12v4"/>'
};
function icon(name){const svg=document.createElementNS("http://www.w3.org/2000/svg","svg");svg.setAttribute("viewBox","0 0 24 24");svg.setAttribute("aria-hidden","true");svg.setAttribute("class","af-icon");svg.innerHTML=shapes[name]||shapes.sparkle;return svg}
function labelButton(id,name){const button=document.getElementById(id);if(!button||button.dataset.afIcon)return;button.dataset.afIcon="1";button.prepend(icon(name))}
function ready(){
const pairs={settlement:"home",wilderness:"map",researchButton:"flask",heroesButton:"users",militaryButton:"shield",expeditionButton:"compass",combatButton:"swords",eventsButton:"sparkle",alliancesButton:"flag",center:"target",missionToggle:"flag",opsToggle:"strategy"};
Object.entries(pairs).forEach(([id,name])=>labelButton(id,name));
const canvas=document.getElementById("world");
if(canvas){
 const quick=document.createElement("nav");quick.className="af-quicklinks";quick.setAttribute("aria-label","ASHFALL quick access");
 for(const [label,href,name] of [["GRAND ARSENAL","/ashfall/arsenal","chest"],["HERO COMMAND","/ashfall/heroes","users"],["CRYSTAL FRONTIER","/ashfall/crystal-frontier","sparkle"]]){
  const a=document.createElement("a");a.className="af-quicklink";a.href=href;a.addEventListener("click",e=>{if(href==="/ashfall/crystal-frontier"&&typeof world!=="undefined"&&world?.state_id){e.preventDefault();window.location.assign(href+"?state_id="+encodeURIComponent(world.state_id))}});a.append(icon(name),document.createTextNode(label));quick.append(a)
 }
 document.body.append(quick);
}
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",ready,{once:true});else ready();
})();