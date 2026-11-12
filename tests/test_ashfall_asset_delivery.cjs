/* ASHFALL 112 — standalone streaming-controller tests.
   Run: node tests/test_ashfall_asset_delivery.cjs
   No npm dependencies, network, browser or production artwork required. */
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const source=fs.readFileSync(path.join(__dirname,"../app/static/ashfall-asset-delivery-107.js"),"utf8");
function harness(manifest){
 const started=[];
 const context={
  console,
  window:{ASHFALL_ART_MANIFEST_116:manifest,ASHFALL_BUILDINGS_100:{
   byKey:{hq:true,farm:true,lumber:true,salvage:true,fuel:true,barracks:true},
   filename:(key,level)=>"/static/ashfall-art/production/"+key+"-standard-"+String(level).padStart(2,"0")+".webp"
  }},
  Image:class {
   constructor(){this.naturalWidth=1024;this.naturalHeight=1024}
   set src(url){this.url=url;started.push(this)}
  }
 };
 vm.runInNewContext(source,context,{filename:"ashfall-asset-delivery-107.js"});
 return {delivery:context.window.ASHFALL_ASSET_DELIVERY_107,started};
}
async function run(){
 const {delivery,started}=harness();
 assert.equal(await delivery.get("invalid",1),null);
 assert.equal(await delivery.get("hq",51),null);
 assert.equal(started.length,0);
 const keys=["hq","farm","lumber","salvage","fuel","barracks"];
 const promises=keys.map(key=>delivery.prefetch(key,1));
 assert.equal(started.length,4,"no more than four active requests");
 assert.equal(delivery.status().queued,2);
 // The last queued request is now visible: it must jump ahead.
 assert.equal(delivery.get("barracks",1,{priority:"high"}),promises[5],"in-flight promise deduplication");
 assert.equal(delivery.status().promotions,1);
 started[0].onload();
 await Promise.resolve();
 assert.ok(started[4].url.includes("barracks"),"visible request is scheduled first");
 for(let i=1;i<started.length;i++)started[i].onload();
 await Promise.all(promises);
 assert.equal(delivery.status().loaded,6);
 assert.equal(delivery.status().active,0);
 const before=started.length;
 assert.ok(await delivery.get("hq",1));
 assert.equal(started.length,before,"cache hit does not start new image request");
 assert.equal(delivery.status().cacheHits,1);
 // Missing image is remembered; it is not requested twice.
 const missing=delivery.get("hq",2);
 started[started.length-1].onerror();
 assert.equal(await missing,null);
 assert.equal(await delivery.get("hq",2),null);
 assert.equal(delivery.status().failures,1);
 const available=["hq-standard-01.webp"];
 const published=harness(available);
 assert.equal(await published.delivery.get("farm",1),null);
 assert.equal(published.started.length,0,"unpublished images must not trigger network requests");
 assert.equal(published.delivery.status().skippedUnpublished,1);
 const loaded=published.delivery.get("hq",1);
 assert.equal(published.started.length,1,"published artwork must still load");
 published.started[0].onload();
 assert.ok(await loaded);
 // A terminal event must settle a request exactly once, even if a browser
 // or image shim invokes a stale handler after completion.
 const repeated=harness(["hq-standard-01.webp"]);
 const first=repeated.delivery.get("hq",1);
 const image=repeated.started[0];
 const staleOnload=image.onload;
 image.onload();
 assert.ok(await first);
 staleOnload();
 assert.equal(repeated.delivery.status().active,0);
 assert.equal(repeated.delivery.status().loaded,1);
 assert.equal(repeated.delivery.status().failures,0);
 // Reject decoded sources above the pixel budget.
 const oversized=harness(["hq-standard-01.webp"]);
 const big=oversized.delivery.get("hq",1);
 oversized.started[0].naturalWidth=4096;
 oversized.started[0].naturalHeight=2048;
 oversized.started[0].onload();
 assert.equal(await big,null);
 assert.equal(oversized.delivery.status().oversized,1);
 assert.equal(oversized.delivery.status().loaded,0);
 assert.equal(oversized.delivery.status().active,0);
 console.log("ASHFALL asset streaming and manifest tests passed.");
}
run().catch(error=>{console.error(error);process.exitCode=1});
