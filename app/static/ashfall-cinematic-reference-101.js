/* ASHFALL 101 — Optional cinematic art direction preview.
   This is a reference image overlay, not a playable settlement or fake game render.
   Hidden unless user explicitly opens it; no game systems modified. */
(function(){
"use strict";
function init(){
 const img="/static/ashfall-art/production/ashfall-cinematic-reference.webp";
 const panel=document.createElement("div");
 panel.id="af-cinematic-reference";
 panel.setAttribute("role","dialog");
 panel.setAttribute("aria-label","ASHFALL cinematic art reference");
 panel.hidden=true;
 panel.innerHTML='<div class="af-cinema-toolbar"><strong>ASHFALL · CINEMATIC ART REFERENCE</strong><span>Illustration only · not the live game world</span><button type="button" id="af-cinema-close">Return to playable settlement ✕</button></div><img alt="Cinematic isometric ASHFALL settlement art direction illustration" src="'+img+'"><div class="af-cinema-note">Visual target: detailed architecture, realistic terrain, atmospheric lighting and cohesive settlement composition. The underlying game remains interactive after closing this preview.</div>';
 const button=document.createElement("button");
 button.id="af-cinema-open";button.type="button";button.textContent="◈ Cinematic Visual Target";
 button.title="Compare the current settlement with the intended visual quality";
 document.body.append(button,panel);
 button.addEventListener("click",()=>{panel.hidden=false;document.body.classList.add("af-cinema-visible")});
 panel.querySelector("#af-cinema-close").addEventListener("click",()=>{panel.hidden=true;document.body.classList.remove("af-cinema-visible")});
 document.addEventListener("keydown",e=>{if(e.key==="Escape"&&!panel.hidden){panel.hidden=true;document.body.classList.remove("af-cinema-visible")}});
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init,{once:true});else init();
})();