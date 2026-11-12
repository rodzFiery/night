/* ASHFALL 107 — Asset delivery controller.
   Controls WebP request concurrency and caches absent assets for the session.
   Designed for 1,000 eventual images without flooding the browser with requests.
   Zero game-state mutations. */
(function(){
"use strict";
const MAX_ACTIVE=4,MAX_CACHE=72;
const loaded=new Map(),missing=new Set(),pending=new Map(),queue=[];
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
  img.onload=()=>finish(true);
  img.onerror=()=>finish(false);
  function finish(ok){
   active--;
   pending.delete(task.url);
   if(ok)touch(task.url,img);else missing.add(task.url);
   task.resolve(ok?img:null);
   emit({key:task.key,level:task.level,url:task.url,ready:ok});
   pump();
  }
  img.src=task.url;
 }
}
function get(key,level){
 if(!valid(key,level))return Promise.resolve(null);
 const url=window.ASHFALL_BUILDINGS_100.filename(key,level);
 if(loaded.has(url)){const img=loaded.get(url);touch(url,img);return Promise.resolve(img)}
 if(missing.has(url))return Promise.resolve(null);
 if(pending.has(url))return pending.get(url);
 let resolve;
 const promise=new Promise(r=>resolve=r);
 pending.set(url,promise);queue.push({key,level,url,resolve});pump();
 return promise;
}
function peek(key,level){
 if(!valid(key,level))return null;
 const url=window.ASHFALL_BUILDINGS_100.filename(key,level);
 return loaded.get(url)||null;
}
window.ASHFALL_ASSET_DELIVERY_107=Object.freeze({
 get,peek,onChange(callback){listeners.add(callback);return()=>listeners.delete(callback)},
 status(){return{loaded:loaded.size,missing:missing.size,active,queued:queue.length,pending:pending.size,maxConcurrent:MAX_ACTIVE,cacheLimit:MAX_CACHE}}
});
})();