/* ASHFALL 13 — Asset-backed architectural art.
   Six original SVG sprite assets; cached, non-blocking, progressive enhancement.
   The existing Canvas geometry remains the fallback when an asset cannot load. */
(function(){
"use strict";
const keys=window.ASHFALL_BUILDINGS_100?.buildings.map(b=>b.key)||["hq","farm","lumber","salvage","fuel","barracks"];
const liveKeys=keys.filter(k=>window.ASHFALL_BUILDINGS_100?.byKey[k]?.status!=="planned");
function artReady(){window.dispatchEvent(new Event("ashfall:art-ready"))}
const sprites=new Map();
const raster=new Map();
const missing=new Set();
const loading=new Set();
// Every building has 25 standard levels and 25 Crystal Era levels.
// Assets are requested lazily, only for buildings actually visible.
// Standard: production/{key}-standard-01.webp ... -25.webp
// Crystal:  production/{key}-crystal-01.webp ... -25.webp
// Until all 1,000 authored assets exist, older tier art and SVG remain fallback.
function stageFor(level){
 const n=Math.max(1,Math.min(50,Math.floor(Number(level)||1)));
 return {era:n<=25?"standard":"crystal",tier:n<=25?n:n-25,level:n};
}
function ready(img){return !!(img&&img.complete&&img.naturalWidth)}
// Compile the published production stages once rather than scanning the
// complete manifest for every building on every settlement redraw.
const publishedStages=new Map();
const productionManifest=window.ASHFALL_ART_MANIFEST_116;
if(Array.isArray(productionManifest)){
 for(const filename of productionManifest){
  const match=/^([a-z][a-z0-9_]*)-(standard|crystal)-(0[1-9]|1[0-9]|2[0-5])\.webp$/.exec(filename);
  if(!match)continue;
  const id=match[1]+":"+match[2];
  if(!publishedStages.has(id))publishedStages.set(id,[]);
  publishedStages.get(id).push(Number(match[3]));
 }
 for(const stages of publishedStages.values())stages.sort((a,b)=>b-a);
}
function nearestPublishedStage(key,era,tier){
 const stages=publishedStages.get(key+":"+era);
 return stages?.find(n=>n<tier)??null;
}
// The delivery controller owns the bounded LRU. Do not retain every decoded
// production bitmap in this renderer: that would defeat the memory budget.
function request(key,era,tier){
 const id=key+":"+era+":"+tier;
 const level=era==="crystal"?tier+25:tier;
 const delivery=window.ASHFALL_ASSET_DELIVERY_107;
 if(delivery){
  const cached=delivery.peek(key,level);
  if(cached)return cached;
  if(missing.has(id)||loading.has(id))return null;
  loading.add(id);
  delivery.get(key,level,{priority:"high"}).then(img=>{
   loading.delete(id);
   if(img)window.dispatchEvent(new Event("ashfall:art-ready"));
   else missing.add(id);
  });
  return null;
 }
 if(raster.has(id)||missing.has(id)||loading.has(id))return raster.get(id)||null;
 loading.add(id);
 const img=new Image();img.decoding="async";
 img.onload=()=>{loading.delete(id);raster.set(id,img);window.dispatchEvent(new Event("ashfall:art-ready"))};
 img.onerror=()=>{loading.delete(id);missing.add(id)};
 img.src="/static/ashfall-art/production/"+key+"-"+era+"-"+String(tier).padStart(2,"0")+".webp?v=1";
 return null;
}
// Original three milestone artworks remain available during migration.
const legacy=new Map();
for(const key of liveKeys)for(const tier of [1,2,3]){
 const img=new Image();img.decoding="async";
 img.onload=artReady;
 img.onerror=()=>{};
 img.src="/static/ashfall-art/production/"+key+"-"+tier+".webp?v=1";
 legacy.set(key+":"+tier,img);
}
function artwork(key,level){
 const stage=stageFor(level);
 const exact=request(key,stage.era,stage.tier);
 if(ready(exact))return exact;
 // If production artwork exists, prefer the nearest earlier authored stage.
 // The manifest prevents nonexistent images from generating network requests.
 const manifest=productionManifest;
 if(Array.isArray(manifest)){
  const earlier=nearestPublishedStage(key,stage.era,stage.tier);
  if(earlier!==null){
   // Queue only the nearest unpublished-in-memory image, but reuse any
   // already-decoded earlier artwork immediately while that request loads.
   const candidate=request(key,stage.era,earlier);
   if(ready(candidate))return candidate;
   const delivery=window.ASHFALL_ASSET_DELIVERY_107;
   const stages=publishedStages.get(key+":"+stage.era)||[];
   for(const previous of stages){
    if(previous>=earlier)continue;
    const cached=delivery?.peek(key,stage.era==="crystal"?previous+25:previous);
    if(ready(cached))return cached;
   }
  }
 }else{
  const step=Math.floor((stage.tier-1)/5)*5+1;
  if(step!==stage.tier){const milestone=request(key,stage.era,step);if(ready(milestone))return milestone;}
 }
 const legacyTier=stage.era==="crystal"?3:stage.tier>=18?3:stage.tier>=9?2:1;
 return [legacy.get(key+":"+legacyTier),legacy.get(key+":2"),legacy.get(key+":1"),sprites.get(key)].find(ready);
}
const config={enabled:true,scale:1,glow:true,quality:"high",maxSourcePixels:4194304};
let loaded=0,failed=0;
for(const key of liveKeys){
 const img=new Image();
 img.decoding="async";
 img.onload=()=>{loaded++;artReady()};
 img.onerror=()=>{failed++;console.warn("ASHFALL art asset unavailable:",key)};
 img.src="/static/ashfall-art/"+key+".svg?v="+94;
 sprites.set(key,img);
}

// ASHFALL 14 — deterministic architectural atmosphere, anchored to each sprite.
// Purely visual: no gameplay, economy, hitboxes, or world coordinates are changed.
function atmosphere(ctx,pos,key,level,constructing,width,height){
 const x=pos.x,y=pos.y;
 const seed=key.split("").reduce((a,ch)=>a*31+ch.charCodeAt(0),17);
 const upgraded=level>=10,elite=level>=30;
 ctx.save();
 // Ground contact shadow and subtle warm ambient bounce.
 const shade=ctx.createRadialGradient(x,y+12,8,x,y+12,width*.48);
 shade.addColorStop(0,"rgba(0,0,0,.42)");
 shade.addColorStop(.58,"rgba(0,0,0,.22)");
 shade.addColorStop(1,"rgba(0,0,0,0)");
 ctx.fillStyle=shade;ctx.beginPath();ctx.ellipse(x,y+12,width*.48,height*.19,0,0,Math.PI*2);ctx.fill();
 if(level>0){
  const glow=ctx.createRadialGradient(x,y-height*.39,1,x,y-height*.39,width*.31);
  glow.addColorStop(0,elite?"rgba(164,130,255,.17)":upgraded?"rgba(255,188,111,.12)":"rgba(255,180,98,.07)");
  glow.addColorStop(1,"rgba(255,180,98,0)");
  ctx.fillStyle=glow;ctx.beginPath();ctx.ellipse(x,y-height*.39,width*.31,height*.35,0,0,Math.PI*2);ctx.fill();
 }
 // Stable architectural floor markers: never flicker between frames.
 ctx.lineWidth=1.2;ctx.strokeStyle=elite?"rgba(179,155,255,.55)":"rgba(225,176,111,.36)";
 for(let i=0;i<4;i++){
  const a=(i*Math.PI/2)+Math.PI/4;
  const px=x+Math.cos(a)*width*.36,py=y+Math.sin(a)*height*.13;
  ctx.beginPath();ctx.moveTo(px-4,py);ctx.lineTo(px+4,py);ctx.stroke();
 }
 // Construction beacon is intentionally restrained to preserve readability.
 if(constructing){
  const by=y-height*.81;
  ctx.fillStyle="rgba(255,184,91,.85)";
  ctx.beginPath();ctx.arc(x+width*.23,by,3.5,0,Math.PI*2);ctx.fill();
 }
 // Individualized atmospheric motes around each facility.
 for(let i=0;i<5;i++){
  const n=(seed+i*73)%97/97;
  const dx=(n-.5)*width*.66;
  const dy=height*(.12+((seed+i*19)%71)/71*.34);
  ctx.fillStyle=elite?"rgba(189,168,255,.35)":"rgba(237,198,142,.25)";
  ctx.fillRect(x+dx,y-dy,1.3,1.3);
 }
 ctx.restore();
}

function render(ctx,pos,b,key,level,constructing){
 if(!config.enabled)return false;
 const img=artwork(key,level);
 if(!img)return false;
 const isRaster=img!==sprites.get(key);
 const size=Math.min(1.15,Math.max(.77,.83+Math.min(level,55)*.005))*config.scale;
 const ratio=isRaster?(img.naturalWidth/img.naturalHeight):(340/266);
 const width=340*size,height=width/ratio;
 // Use high-resolution source artwork while preserving the existing world footprint.
 // Rendering resolution is governed by the main canvas DPR, not sprite CSS dimensions.
 // Existing building position is the center of its roof.
 // Offset sprite downward to align the illustrated plinth with the footprint.
 const groundY=pos.y+b.height+level*4;
 const left=pos.x-width/2,top=groundY-height*.93;
 ctx.save();
 if(config.glow&&level>30){
  const strength=Math.min(28,8+(level-30)*.7);
  ctx.shadowColor="#a98aff";ctx.shadowBlur=strength;
 }
 window.ASHFALL_BUILDING_LIGHT_110?.ground(ctx,pos.x,groundY,width,height,key,level);
 window.ASHFALL_BUILDING_LIGHT_110?.silhouette(ctx,img,left,top,width,height);
 atmosphere(ctx,{x:pos.x,y:groundY},key,level,constructing,width,height);
 ctx.imageSmoothingEnabled=true;
 ctx.imageSmoothingQuality=config.quality==="low"?"medium":"high";
 ctx.drawImage(img,left,top,width,height);
 window.ASHFALL_BUILDING_LIGHT_110?.material(ctx,left,top,width,height,level);
 ctx.shadowBlur=0;
 window.ASHFALL_ART_EVOLUTION?.draw(ctx,left,top,width,height,key,level);
 window.ASHFALL_ARCHITECTURAL_TIERS_103?.draw(ctx,left,top,width,height,key,level);
 if(constructing){
  ctx.strokeStyle="#f1c083";ctx.lineWidth=2;
  ctx.setLineDash([7,5]);
  ctx.strokeRect(left+width*.13,top+height*.21,width*.74,height*.69);
  ctx.setLineDash([]);
 }
 ctx.restore();
 return true;
}
window.ASHFALL_ART={render,config,stageFor,status:()=>({loaded,failed,total:liveKeys.length,rasterReady:window.ASHFALL_ASSET_DELIVERY_107?.status().loaded??[...raster.values()].filter(ready).length,requested:raster.size+missing.size+loading.size,missing:missing.size,eras:2,levelsPerEra:25})};
})();