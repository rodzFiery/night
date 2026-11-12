/* ASHFALL 44 — Economic Doctrine Console.
   Server-authoritative doctrine selection. All bonuses and cooldowns originate
   from /ashfall/api/economy; this UI never changes balances locally. */
(function(){
"use strict";
const $=id=>document.getElementById(id);
const choices=[
 ["balanced","BALANCED","No production bonus"],
 ["agriculture","AGRICULTURE","+8% food production"],
 ["forestry","FORESTRY","+8% wood production"],
 ["industry","INDUSTRY","+8% metal production"],
 ["energy","ENERGY","+8% gas production"]
];
let data=null,context=null,busy=false;
function ensure(){
 const panel=$("buildpanel");if(!panel)return null;
 let root=$("afDoctrine44");
 if(root){
  const target=$("afView40-strategy");
  if(target&&root.parentElement!==target)target.append(root);
  return root;
 }
 root=document.createElement("section");root.id="afDoctrine44";root.className="af-doctrine44";
 root.setAttribute("aria-label","Economic specialization doctrine");
 const heading=document.createElement("div");heading.className="af-doctrine-head44";
 const title=document.createElement("strong");title.textContent="ECONOMIC DOCTRINE";
 const status=document.createElement("span");status.id="afDoctrineStatus44";
 heading.append(title,status);
 const intro=document.createElement("p");intro.textContent="Specialize your Haven's conventional production. Switching doctrines has a 24-hour cooldown.";
 const options=document.createElement("div");options.className="af-doctrine-options44";
 for(const [key,label,description] of choices){
  const button=document.createElement("button");button.type="button";button.dataset.afDoctrine=key;
  const name=document.createElement("strong");name.textContent=label;
  const info=document.createElement("small");info.textContent=description;
  button.append(name,info);
  button.onclick=()=>choose(key);
  options.append(button);
 }
 const message=document.createElement("p");message.id="afDoctrineMessage44";message.setAttribute("role","status");
 root.append(heading,intro,options,message);
 const target=$("afView40-strategy");
 if(target)target.append(root);else panel.append(root);
 return root;
}
function render(){
 if(!ensure())return;
 const doctrine=data?.doctrine;
 const status=$("afDoctrineStatus44"),message=$("afDoctrineMessage44");
 if(!doctrine){status.textContent="UNAVAILABLE";message.textContent="Waiting for the authoritative economy snapshot.";return}
 status.textContent=String(doctrine.focus).replaceAll("_"," ").toUpperCase();
 if(!busy){
  const remaining=Math.max(0,Number(doctrine.next_change_at||0)-Number(data.server_time||0));
  message.textContent=doctrine.can_change?"You may choose a doctrine. Your selection affects future production only.":
    "Doctrine locked for "+Math.ceil(remaining/3600)+" more hour(s).";
 }
 for(const button of document.querySelectorAll("[data-af-doctrine]")){
  const selected=button.dataset.afDoctrine===doctrine.focus;
  button.setAttribute("aria-pressed",String(selected));
  button.disabled=busy||selected||!doctrine.can_change||!context?.csrf_token||!context?.state_id;
 }
}
async function choose(focus){
 if(busy||!data?.doctrine?.can_change||!context?.csrf_token||!context?.state_id)return;
 busy=true;render();
 $("afDoctrineMessage44").textContent="Confirming doctrine with the Haven server…";
 try{
  const body=new URLSearchParams({csrf_token:context.csrf_token,state_id:String(context.state_id),focus});
  const response=await fetch("/ashfall/api/economy/doctrine",{
   method:"POST",credentials:"same-origin",
   headers:{"Content-Type":"application/x-www-form-urlencoded"},body
  });
  const payload=await response.json();
  if(!response.ok)throw Error(typeof payload.detail==="string"?payload.detail:"Doctrine change failed");
  data=payload;
  window.ASHFALL_ROSTER36?.sync(payload);
  window.ASHFALL_UPGRADE_INTEL37?.sync(payload);
  window.ASHFALL_PRIORITIES38?.sync(payload);
  window.ASHFALL_STRATEGY39?.sync(payload);
  $("afDoctrineMessage44").textContent="Doctrine confirmed by the Haven server.";
  window.dispatchEvent(new CustomEvent("ashfall:doctrine-updated",{detail:payload}));
 }catch(error){$("afDoctrineMessage44").textContent=error.message||"Doctrine change failed"}
 finally{busy=false;render()}
}
function sync(next){data=next;render()}
function configure(next){context=next;render()}
window.ASHFALL_DOCTRINE44={sync,configure};
})();
