#!/usr/bin/env node
/* ASHFALL 61 — deterministic planner contract checks without a browser.
 * The production module is loaded unmodified in a sandboxed Node VM.
 */
"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const source=fs.readFileSync(path.join(__dirname,"../app/static/ashfall-development-planner-55.js"),"utf8");
const window={};
vm.runInNewContext(source,{window,document:{getElementById(){return null}}},{filename:"ashfall-development-planner-55.js",timeout:2000});
const {analyze,roadmapAudit,scenarioComparison,rankScenarios,developmentMilestones}=window.ASHFALL_PLANNER55;
const fixture={
 resources:{food:250,wood:40,metal:10,gas:0},
 rare_materials:{crystal_shards:0},
 production_rates:{
  food:{per_hour:100},wood:{per_hour:20},metal:{per_hour:0},gas:{per_hour:0}
 },
 queue:null,
 buildings:{
  farm:{name:"Farm",level:1,max_level:55,unlocked:true,cost:{wood:50,metal:10},rare_cost:{}},
  hq:{name:"Command Center",level:1,max_level:55,unlocked:true,cost:{wood:30,food:60},rare_cost:{}},
  fuel:{name:"Fuel",level:30,max_level:55,unlocked:true,cost:{wood:10},rare_cost:{crystal_shards:2}}
 }
};
function test(name,run){run();process.stdout.write("PASS "+name+"\n")}
test("single facility timing uses server hourly rate",()=>{
 const item=analyze("farm",fixture);
 assert.equal(item.eligible,false);
 assert.equal(item.hours,.5);
 assert.equal(item.shortages.length,1);
});
test("cumulative reservations match sequential roadmap",()=>{
 const result=roadmapAudit(fixture,["farm","hq"]);
 assert.equal(result.totals.wood,80);
 assert.equal(result.totals.food,60);
 assert.equal(result.steps[0].shortages.wood,10);
 assert.equal(result.steps[1].shortages.wood,40);
 const wood=result.bottlenecks.find(row=>row.resource==="wood");
 assert.equal(wood.deficit,40);
 assert.equal(wood.hours,2);
});
test("reordering preserves totals but changes per-step shortages",()=>{
 const a=roadmapAudit(fixture,["farm","hq"]);
 const b=roadmapAudit(fixture,["hq","farm"]);
 assert.equal(a.totals.wood,b.totals.wood);
 assert.equal(b.steps[0].shortages.wood,undefined);
 assert.equal(b.steps[1].shortages.wood,40);
});
test("rare material is blocked without fabricated production",()=>{
 const result=roadmapAudit(fixture,["fuel"]);
 const rare=result.bottlenecks.find(row=>row.resource==="crystal_shards");
 assert.equal(rare.deficit,2);
 assert.equal(rare.rare,true);
 assert.equal(rare.hours,Infinity);
});
test("missing production data is unknown, not zero or ready",()=>{
 const data=structuredClone(fixture);
 delete data.production_rates.wood;
 const report=roadmapAudit(data,["farm"]);
 const wood=report.bottlenecks.find(row=>row.resource==="wood");
 assert.equal(wood.known,false);
 assert.equal(wood.hours,Infinity);
 assert.equal(analyze("farm",data).hours,Infinity);
});
test("negative and nonnumeric rates cannot yield a false ETA",()=>{
 for(const invalid of [-10,"unavailable",""]){
  const data=structuredClone(fixture);
  data.production_rates.wood.per_hour=invalid;
  assert.equal(roadmapAudit(data,["farm"]).bottlenecks.find(row=>row.resource==="wood").hours,Infinity);
  assert.equal(analyze("farm",data).hours,Infinity);
 }
});
test("max-level facilities and occupied construction slots are blocked",()=>{
 const data=structuredClone(fixture);
 data.buildings.farm.level=55;
 assert.equal(analyze("farm",data).max,true);
 data.buildings.farm.level=1;
 data.queue={building_key:"hq"};
 assert.equal(analyze("farm",data).eligible,false);
});
test("scenario boost changes only the selected resource rate",()=>{
 const original=structuredClone(fixture);
 const report=scenarioComparison(fixture,["farm","hq"],"wood",100);
 const wood=report.rows.find(row=>row.resource==="wood");
 assert.equal(wood.hours,2);
 assert.equal(wood.scenarioHours,1);
 assert.equal(wood.hoursSaved,1);
 assert.equal(report.baselineHours,2);
 assert.equal(report.scenarioHours,1);
 assert.deepEqual(fixture,original,"Scenario mutated the authoritative snapshot");
});
test("zero boost matches baseline",()=>{
 const report=scenarioComparison(fixture,["farm","hq"],"wood",0);
 assert.equal(report.baselineHours,report.scenarioHours);
});
test("rare-material blockers persist under production boosts",()=>{
 const report=scenarioComparison(fixture,["fuel"],"wood",100);
 assert.equal(report.baselineHours,Infinity);
 assert.equal(report.scenarioHours,Infinity);
});
test("zero production cannot be created by percentage boosts",()=>{
 const data=structuredClone(fixture);
 data.buildings.farm.cost={metal:20};
 const report=scenarioComparison(data,["farm"],"metal",100);
 assert.equal(report.rows.find(row=>row.resource==="metal").scenarioHours,Infinity);
});
test("scenario ranking favors the greatest reduction in roadmap wait",()=>{
 const ranking=rankScenarios(fixture,["farm","hq"],100);
 assert.equal(ranking.length,4);
 assert.equal(ranking[0].resource,"wood");
 assert.equal(ranking[0].gain,1);
 assert.equal(ranking[1].gain,0);
});
test("scenario ranking is deterministic under equal gains",()=>{
 const ranking=rankScenarios(fixture,["farm","hq"],0);
 assert.deepEqual(ranking.map(row=>row.resource),["food","wood","metal","gas"]);
});
test("blocked rare materials never create imaginary global savings",()=>{
 const ranking=rankScenarios(fixture,["fuel"],100);
 assert.equal(ranking.every(row=>row.blocked&&row.gain===0),true);
});
test("ranking never mutates authoritative resource rates",()=>{
 const before=structuredClone(fixture);
 rankScenarios(fixture,["farm","hq"],50);
 assert.deepEqual(fixture,before);
});
test("milestones use actual building levels, not planned upgrades",()=>{
 const original=structuredClone(fixture);
 const before=developmentMilestones(fixture,[]);
 const after=developmentMilestones(fixture,["farm","hq"]);
 assert.deepEqual(after.tiers,before.tiers);
 assert.equal(before.next.target,5);
 assert.equal(before.next.reached,1);
 assert.equal(before.next.total,3);
 assert.equal(before.priority.key,"hq");
 assert.deepEqual(fixture,original);
});
test("milestones complete only when every available facility reaches threshold",()=>{
 const data=structuredClone(fixture);
 for(const key of Object.keys(data.buildings))data.buildings[key].level=50;
 const status=developmentMilestones(data,[]);
 assert.equal(status.next,null);
 assert.equal(status.tiers.every(tier=>tier.complete&&tier.percent===100),true);
});
test("milestone priority identifies the lowest-level unfinished facility",()=>{
 const data=structuredClone(fixture);
 data.buildings.hq.level=15;
 data.buildings.farm.level=4;
 data.buildings.fuel.level=2;
 const status=developmentMilestones(data,["fuel"]);
 assert.equal(status.priority.key,"fuel");
 assert.equal(status.plannedTowardNext[0],"fuel");
});
process.stdout.write("ASHFALL planner contract suite passed\n");
