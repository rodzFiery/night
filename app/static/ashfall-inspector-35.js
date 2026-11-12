/* ASHFALL 35 — Inspector focus and mobile panel hierarchy.
   Presentation only: no economy mutations, no changes to game state. */
(function(){
"use strict";
const $=id=>document.getElementById(id);
const panel=$("buildpanel");
if(!panel)return;
let previousFocus=null;
let open=false;
const close=document.createElement("button");
close.type="button";
close.id="afInspectorClose35";
close.className="af-inspector-close35";
close.setAttribute("aria-label","Close building inspector");
close.textContent="×";
panel.insertBefore(close,panel.firstChild);
panel.setAttribute("aria-label","Building inspector");
panel.setAttribute("role","region");
function sync(){
 const visible=!panel.hidden;
 document.body.classList.toggle("af-inspector-open35",visible);
 if(visible&&!open){
  previousFocus=document.activeElement instanceof HTMLElement?document.activeElement:null;
 }
 if(!visible&&open&&previousFocus&&previousFocus.isConnected){
  // Do not steal focus from another control chosen by the player.
  if(document.activeElement===document.body||panel.contains(document.activeElement)){
   previousFocus.focus({preventScroll:true});
  }
 }
 open=visible;
}
function dismiss(){
 if(panel.hidden)return;
 panel.hidden=true;
 sync();
}
close.addEventListener("click",dismiss);
document.addEventListener("keydown",event=>{
 if(event.key!=="Escape"||panel.hidden||event.defaultPrevented)return;
 const modal=document.getElementById("commandOverlay");
 if(modal&&!modal.hidden)return;
 const active=document.activeElement;
 if(active&&active.closest&&active.closest('[role="dialog"]:not([hidden])'))return;
 event.preventDefault();
 dismiss();
});
const observer=new MutationObserver(sync);
observer.observe(panel,{attributes:true,attributeFilter:["hidden"]});
sync();
window.ASHFALL_INSPECTOR35={dismiss,sync};
})();
