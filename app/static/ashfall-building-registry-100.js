/* ASHFALL 100 — 15-facility, 50-stage visual-production registry.
   Six existing gameplay facilities are live. Nine future facilities are art
   reservations only: never pretend they have server-side economy mechanics. */
(function(){
"use strict";
const entries=[
 ["hq","Command Center","live"],["farm","Farm","live"],["lumber","Lumber Yard","live"],
 ["salvage","Salvage Station","live"],["fuel","Fuel Collector","live"],["barracks","Barracks","live"],
 ["research","Research Institute","planned"],["hospital","Field Hospital","planned"],
 ["warehouse","Supply Warehouse","planned"],["refinery","Metal Refinery","planned"],
 ["power","Power Plant","planned"],["wall","Defense Headquarters","planned"],
 ["radar","Radar Station","planned"],["workshop","Engineering Workshop","planned"],
 ["embassy","Alliance Embassy","planned"]
];
const buildings=Object.freeze(entries.map(([key,name,status])=>Object.freeze({key,name,status,standardLevels:25,crystalLevels:25})));
const byKey=Object.freeze(Object.fromEntries(buildings.map(b=>[b.key,b])));
function stage(level){
 const n=Math.max(1,Math.min(50,Math.floor(Number(level)||1)));
 return Object.freeze({overall:n,era:n<=25?"standard":"crystal",eraLevel:n<=25?n:n-25});
}
function filename(key,level){
 if(!byKey[key])return null;
 const s=stage(level);
 return "/static/ashfall-art/production/"+key+"-"+s.era+"-"+String(s.eraLevel).padStart(2,"0")+".webp";
}
window.ASHFALL_BUILDINGS_100=Object.freeze({buildings,byKey,stage,filename,
 summary:()=>({buildings:buildings.length,live:buildings.filter(b=>b.status==="live").length,
 planned:buildings.filter(b=>b.status==="planned").length,levelsPerBuilding:50,visualStages:buildings.length*50})});
})();