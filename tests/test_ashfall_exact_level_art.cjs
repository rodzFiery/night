/* ASHFALL 133: exact-level renderer contract; run with node. */
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const source=fs.readFileSync(path.join(__dirname,"../app/static/ashfall-art-13.js"),"utf8");
function load(manifest){
 const requests=[];
 class FakeImage {
  constructor(){this.complete=false;this.naturalWidth=0;this.naturalHeight=0}
  set src(value){
   this.url=value;requests.push(value);
   if(value.endsWith(".svg?v=94")){
    this.complete=true;this.naturalWidth=340;this.naturalHeight=266;
   }
  }
 }
 const window={
  ASHFALL_ART_MANIFEST_116:manifest,
  ASHFALL_BUILDINGS_100:{buildings:[{key:"hq",status:"live"}],byKey:{hq:{status:"live"}}},
  dispatchEvent:()=>{},
 };
 const context={window,Image:FakeImage,Event:class Event{},console};
 vm.runInNewContext(source,context);
 return {window,requests};
}
{
 const {window,requests}=load(["hq-standard-01.webp","hq-standard-13.webp","hq-crystal-01.webp"]);
 assert.equal(window.ASHFALL_ART.stageFor(25).era,"standard");
 assert.equal(window.ASHFALL_ART.stageFor(26).era,"crystal");
 assert.equal(window.ASHFALL_ART.stageFor(50).tier,25);
 assert.equal(window.ASHFALL_ART.status().exactLevelOnly,true);
 // Missing level 12 must not silently request stage 01 or 13.
 const draw=window.ASHFALL_ART.render;
 const noOp=()=>{};
 const ctx={save:noOp,restore:noOp,createRadialGradient:()=>({addColorStop:noOp}),
  beginPath:noOp,ellipse:noOp,fill:noOp,stroke:noOp,moveTo:noOp,lineTo:noOp,
  fillRect:noOp,drawImage:noOp,strokeRect:noOp,setLineDash:noOp,arc:noOp};
 assert.equal(draw(ctx,{x:0,y:0},{height:10},"hq",12,false),true);
 assert.equal(requests.filter(url=>url.includes("hq-standard-12.webp")).length,0);
 assert.equal(requests.filter(url=>url.includes("hq-standard-01.webp")).length,0);
 // Published stage 13 may be requested, but stage 12 never maps to it.
 draw(ctx,{x:0,y:0},{height:10},"hq",13,false);
 assert.equal(requests.filter(url=>url.includes("hq-standard-13.webp")).length,1);
}
console.log("ASHFALL exact-level artwork mapping: passed");
