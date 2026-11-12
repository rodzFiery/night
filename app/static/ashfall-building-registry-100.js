/* ASHFALL 100 — provisional facility registry, 50-stage visual-production contract.
   Six existing gameplay facilities are live. Nine future facilities are art
   reservations only: never pretend they have server-side economy mechanics. */
(function(){
"use strict";
const entries=[
 ["hq","Command Center","live"],["farm","Farm","live"],["lumber","Lumber Yard","live"],
 ["salvage","Salvage Station","live"],["fuel","Fuel Collector","live"],["barracks","Barracks","live"],
 ["hero_base","Hero Base","planned"],["tavern","Tavern","planned"],
 ["rider_garage","Rider Garage","planned"],["hunter_range","Hunter Range","planned"],
 ["hospital","Hospital","planned"],["research","Research Laboratory","planned"],
 ["training","Training Grounds","planned"],["refinery","Metal Refinery","planned"],
 ["warehouse","Warehouse","planned"],["wall","Wall & Watchtowers","planned"],
 ["alliance","Alliance Center","planned"],["recon","Recon Center","planned"],
 ["workshop","Workshop","planned"]
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