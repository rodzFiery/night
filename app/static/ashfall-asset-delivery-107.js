/* ASHFALL 107 — Asset delivery controller.
   Controls WebP request concurrency and caches absent assets for the session.
   Designed for 1,000 eventual images without flooding the browser with requests.
   Zero game-state mutations. */
(function(){
"use strict";
const MAX_ACTIVE=4,MAX_CACHE=48,MAX_PIXELS=4194304;
const loaded=new Map(),missing=new Set(),pending=new Map(),queue=[];
const counters={requests:0,cacheHits:0,promotions:0,failures:0,oversized:0,skippedUnpublished:0};
const manifest=Array.isArray(window.ASHFALL_ART_MANIFEST_116)?new Set(window.ASHFALL_ART_MANIFEST_116):null;
function published(url){return !manifest||manifest.has(url.slice(url.lastIndexOf("/")+1))}
let active=0;
const listeners=new Set();
function emit(detail){for(const listener of listeners){try{listener(detail)}catch(e){console.warn("ASHFALL asset listener failed",e)}}}
function valid(key,level){
 const reg=window.ASHFALL_BUILDINGS_100;
 return !!(reg?.byKey?.[key]&&Number.isInteger(level)&&level>=1&&level<=50);
}
function touch(url,img){
 loaded.delete(url);loaded.set(url,img);
 while(loaded.size>MAX_CACHE){const oldest=loaded.keys().next().value;loaded.delete(oldest)}
}
function pump(){
 while(active<MAX_ACTIVE&&queue.length){
  const task=queue.shift();
  if(!task||!pending.has(task.url))continue;
  active++;
  const img=new Image();img.decoding="async";
  let settled=false;
  img.onload=()=>{const validSize=!!img.naturalWidth&&!!img.naturalHeight;const oversized=validSize&&img.naturalWidth*img.naturalHeight>MAX_PIXELS;if(oversized)counters.oversized++;finish(validSize&&!oversized)};
  img.onerror=()=>finish(false);
  function finish(ok){
   // Some image implementations can report more than one terminal event.
   // A request must release its concurrency slot exactly once.
   if(settled)return;
   settled=true;
   img.onload=null;img.onerror=null;
   active--;
   pending.delete(task.url);
   if(ok)touch(task.url,img);else{missing.add(task.url);counters.failures++;}
   task.resolve(ok?img:null);
   emit({key:task.key,level:task.level,url:task.url,ready:ok});
   pump();
  }
  try{img.src=task.url}catch(_error){finish(false)}
 }
}
function get(key,level,options){
 if(!valid(key,level))return Promise.resolve(null);
 const url=window.ASHFALL_BUILDINGS_100.filename(key,level);
 if(!published(url)){counters.skippedUnpublished++;return Promise.resolve(null)}
 if(loaded.has(url)){counters.cacheHits++;const img=loaded.get(url);touch(url,img);return Promise.resolve(img)}
 if(missing.has(url))return Promise.resolve(null);
 if(pending.has(url)){
  if(options?.priority==="high"){
   const index=queue.findIndex(task=>task.url===url);
   if(index>0){const [task]=queue.splice(index,1);queue.unshift(task);counters.promotions++;}
  }
  return pending.get(url);
 }
 let resolve;
 const promise=new Promise(r=>resolve=r);
 pending.set(url,promise);counters.requests++;
 const task={key,level,url,resolve};
 if(options?.priority==="high")queue.unshift(task);else queue.push(task);
 pump();
 return promise;
}
function peek(key,level){
 if(!valid(key,level))return null;
 const url=window.ASHFALL_BUILDINGS_100.filename(key,level);
 return published(url)?loaded.get(url)||null:null;
}
window.ASHFALL_ASSET_DELIVERY_107=Object.freeze({
 get,peek,prefetch(key,level){return get(key,level,{priority:"low"})},onChange(callback){listeners.add(callback);return()=>listeners.delete(callback)},
 status(){return{loaded:loaded.size,missing:missing.size,active,queued:queue.length,pending:pending.size,maxConcurrent:MAX_ACTIVE,cacheLimit:MAX_CACHE,maxSourcePixels:MAX_PIXELS,manifestEntries:manifest?.size??null,...counters}}
});
})();