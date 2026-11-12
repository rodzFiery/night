"""ASHFALL Crystal Frontier: persistent missions, refinery, discoveries, and research.

All resource mutation is server-authoritative and must be called inside BEGIN IMMEDIATE.
"""
import hashlib
import time
from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pathlib import Path
from app import ashfall_crystal_age as crystal

MISSIONS = {
    "fractured_quarry": {"name":"Fractured Quarry", "min_hq":30, "duration":1800, "cost":{"food":800,"metal":500}, "reward":{"crystal_shards":35,"ancient_cores":1,"prismatic_essence":0}, "risk":"low"},
    "buried_reactor": {"name":"Buried Reactor", "min_hq":32, "duration":7200, "cost":{"metal":1500,"gas":600}, "reward":{"crystal_shards":95,"ancient_cores":3,"prismatic_essence":1}, "risk":"moderate"},
    "prismatic_rift": {"name":"Prismatic Rift", "min_hq":36, "duration":14400, "cost":{"food":2400,"gas":1200}, "reward":{"crystal_shards":175,"ancient_cores":5,"prismatic_essence":3}, "risk":"high"},
    "ancient_vault": {"name":"Ancient Vault", "min_hq":42, "duration":28800, "cost":{"metal":4500,"gas":2400}, "reward":{"crystal_shards":340,"ancient_cores":12,"prismatic_essence":7}, "risk":"extreme"},
}
RESEARCH = {
    "resonance_mapping": {"name":"Resonance Mapping","max":5,"requires":None,"shards":40,"cores":2,"essence":0,"description":"Improves all Crystal Frontier expedition yields by 5% per level."},
    "crystal_refining": {"name":"Crystal Refining","max":5,"requires":"resonance_mapping","shards":90,"cores":4,"essence":1,"description":"Improves refinery output by 10% per level."},
    "void_cartography": {"name":"Void Cartography","max":5,"requires":"resonance_mapping","shards":120,"cores":5,"essence":2,"description":"Reduces expedition travel duration by 5% per level."},
    "prismatic_architecture": {"name":"Prismatic Architecture","max":5,"requires":"crystal_refining","shards":180,"cores":8,"essence":3,"description":"Reduces Crystal Age rare-material building costs by 3% per level."},
}
RECIPES = {
    "core_synthesis":{"name":"Core Synthesis","cost":{"crystal_shards":90},"output":{"ancient_cores":2},"requires":"crystal_refining"},
    "essence_distillation":{"name":"Essence Distillation","cost":{"crystal_shards":150,"ancient_cores":5},"output":{"prismatic_essence":2},"requires":"crystal_refining"},
}
ACHIEVEMENTS = {
    "first_signal":{"name":"First Signal","description":"Launch a Crystal Frontier expedition"},
    "frontier_veteran":{"name":"Frontier Veteran","description":"Complete 10 expeditions"},
    "deep_explorer":{"name":"Deep Explorer","description":"Complete 50 expeditions"},
    "crystal_scholar":{"name":"Crystal Scholar","description":"Complete 10 Crystal Age research levels"},
    "master_refiner":{"name":"Master Refiner","description":"Perform 20 refining operations"},
}
def initialize(db):
    crystal.initialize(db)
    db.execute("""CREATE TABLE IF NOT EXISTS ashfall_crystal_frontier_missions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
        mission_key TEXT NOT NULL, launched_at REAL NOT NULL, completes_at REAL NOT NULL,
        claimed_at REAL, reward_json TEXT NOT NULL)""")
    db.execute("CREATE INDEX IF NOT EXISTS ashfall_crystal_frontier_by_haven ON ashfall_crystal_frontier_missions(haven_id,claimed_at)")
    db.execute("""CREATE TABLE IF NOT EXISTS ashfall_crystal_frontier_research(
        haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
        tech_key TEXT NOT NULL, level INTEGER NOT NULL DEFAULT 0 CHECK(level BETWEEN 0 AND 5),
        PRIMARY KEY(haven_id,tech_key))""")
    db.execute("""CREATE TABLE IF NOT EXISTS ashfall_crystal_frontier_stats(
        haven_id INTEGER PRIMARY KEY REFERENCES ashfall_havens(id) ON DELETE CASCADE,
        expeditions_completed INTEGER NOT NULL DEFAULT 0,
        refining_operations INTEGER NOT NULL DEFAULT 0)""")
    db.execute("""CREATE TABLE IF NOT EXISTS ashfall_crystal_frontier_achievements(
        haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
        achievement_key TEXT NOT NULL, earned_at REAL NOT NULL,
        PRIMARY KEY(haven_id,achievement_key))""")

def ensure(db,hid):
    crystal.prepare(db,hid)
    db.execute("INSERT OR IGNORE INTO ashfall_crystal_frontier_stats(haven_id) VALUES(?)",(hid,))

def hq_level(db,hid):
    row=db.execute("SELECT level FROM ashfall_building_levels WHERE haven_id=? AND building_key='hq'",(hid,)).fetchone()
    return int(row[0]) if row else 0

def levels(db,hid):
    return {r["tech_key"]:int(r["level"]) for r in db.execute("SELECT tech_key,level FROM ashfall_crystal_frontier_research WHERE haven_id=?",(hid,))}

def earn(db,hid,key,now):
    db.execute("INSERT OR IGNORE INTO ashfall_crystal_frontier_achievements(haven_id,achievement_key,earned_at) VALUES(?,?,?)",(hid,key,now))

def spend_rare(db,hid,cost):
    current=crystal.balance(db,hid)
    if any(current.get(k,0)<v for k,v in cost.items()):
        raise ValueError("Insufficient rare materials")
    db.execute("UPDATE ashfall_crystal_balances SET crystal_shards=crystal_shards-?,ancient_cores=ancient_cores-?,prismatic_essence=prismatic_essence-? WHERE haven_id=?",
        (cost.get("crystal_shards",0),cost.get("ancient_cores",0),cost.get("prismatic_essence",0),hid))

def award_rare(db,hid,reward):
    db.execute("UPDATE ashfall_crystal_balances SET crystal_shards=crystal_shards+?,ancient_cores=ancient_cores+?,prismatic_essence=prismatic_essence+? WHERE haven_id=?",
        (reward.get("crystal_shards",0),reward.get("ancient_cores",0),reward.get("prismatic_essence",0),hid))

def mission_reward(key,lv,nonce):
    import json
    definition=MISSIONS[key]
    # Fixed deterministic yields; research upgrades are locked in at launch.
    boost=1+0.05*lv.get("resonance_mapping",0)
    return {k:int(v*boost) for k,v in definition["reward"].items()}

def launch(db,hid,key,now=None):
    import json
    now=time.time() if now is None else now
    if key not in MISSIONS:raise ValueError("Unknown expedition")
    ensure(db,hid)
    definition=MISSIONS[key]
    if hq_level(db,hid)<definition["min_hq"]:raise ValueError("Command Center level too low")
    active=db.execute("SELECT COUNT(*) FROM ashfall_crystal_frontier_missions WHERE haven_id=? AND claimed_at IS NULL",(hid,)).fetchone()[0]
    if active>=3:raise ValueError("All three expedition slots are occupied")
    balance=db.execute("SELECT food,wood,metal,gas FROM ashfall_resource_balances WHERE haven_id=?",(hid,)).fetchone()
    if not balance or any(balance[k]<v for k,v in definition["cost"].items()):raise ValueError("Insufficient expedition supplies")
    lv=levels(db,hid)
    duration=max(300,int(definition["duration"]*(1-.05*lv.get("void_cartography",0))))
    reward=mission_reward(key,lv,now)
    db.execute("UPDATE ashfall_resource_balances SET food=food-?,wood=wood-?,metal=metal-?,gas=gas-? WHERE haven_id=?",
        (*(definition["cost"].get(k,0) for k in ("food","wood","metal","gas")),hid))
    cur=db.execute("INSERT INTO ashfall_crystal_frontier_missions(haven_id,mission_key,launched_at,completes_at,reward_json) VALUES(?,?,?,?,?)",
        (hid,key,now,now+duration,json.dumps(reward,sort_keys=True)))
    earn(db,hid,"first_signal",now)
    return {"mission_id":cur.lastrowid,"completes_at":now+duration,"reward":reward}

def claim(db,hid,mission_id,now=None):
    import json
    now=time.time() if now is None else now
    row=db.execute("SELECT * FROM ashfall_crystal_frontier_missions WHERE id=? AND haven_id=?",(mission_id,hid)).fetchone()
    if not row:raise ValueError("Expedition not found")
    if row["claimed_at"] is not None:raise ValueError("Expedition already claimed")
    if now<float(row["completes_at"]):raise ValueError("Expedition is still underway")
    reward=json.loads(row["reward_json"])
    award_rare(db,hid,reward)
    db.execute("UPDATE ashfall_crystal_frontier_missions SET claimed_at=? WHERE id=? AND claimed_at IS NULL",(now,mission_id))
    db.execute("UPDATE ashfall_crystal_frontier_stats SET expeditions_completed=expeditions_completed+1 WHERE haven_id=?",(hid,))
    count=db.execute("SELECT expeditions_completed FROM ashfall_crystal_frontier_stats WHERE haven_id=?",(hid,)).fetchone()[0]
    if count>=10:earn(db,hid,"frontier_veteran",now)
    if count>=50:earn(db,hid,"deep_explorer",now)
    return reward

def research_cost(key,level):
    d=RESEARCH[key]
    return {"crystal_shards":d["shards"]*(level+1),"ancient_cores":d["cores"]*(level+1),"prismatic_essence":d["essence"]*(level+1)}

def upgrade_research(db,hid,key,now=None):
    now=time.time() if now is None else now
    if key not in RESEARCH:raise ValueError("Unknown technology")
    if hq_level(db,hid)<30:raise ValueError("Crystal Age is locked")
    lv=levels(db,hid);current=lv.get(key,0);definition=RESEARCH[key]
    if current>=definition["max"]:raise ValueError("Technology already mastered")
    prereq=definition["requires"]
    if prereq and lv.get(prereq,0)<1:raise ValueError("Research prerequisite not met")
    cost=research_cost(key,current)
    spend_rare(db,hid,cost)
    db.execute("INSERT INTO ashfall_crystal_frontier_research(haven_id,tech_key,level) VALUES(?,?,1) ON CONFLICT(haven_id,tech_key) DO UPDATE SET level=level+1",(hid,key))
    total=sum(lv.values())+1
    if total>=10:earn(db,hid,"crystal_scholar",now)
    return {"tech_key":key,"level":current+1,"cost":cost}

def refine(db,hid,key,now=None):
    now=time.time() if now is None else now
    if key not in RECIPES:raise ValueError("Unknown recipe")
    if hq_level(db,hid)<30:raise ValueError("Crystal Age is locked")
    lv=levels(db,hid);d=RECIPES[key]
    if lv.get(d["requires"],0)<1:raise ValueError("Research Crystal Refining first")
    spend_rare(db,hid,d["cost"])
    multiplier=1+.10*lv.get("crystal_refining",0)
    reward={k:int(v*multiplier) for k,v in d["output"].items()}
    award_rare(db,hid,reward)
    db.execute("UPDATE ashfall_crystal_frontier_stats SET refining_operations=refining_operations+1 WHERE haven_id=?",(hid,))
    count=db.execute("SELECT refining_operations FROM ashfall_crystal_frontier_stats WHERE haven_id=?",(hid,)).fetchone()[0]
    if count>=20:earn(db,hid,"master_refiner",now)
    return reward

def snapshot(db,hid,now=None):
    import json
    now=time.time() if now is None else now
    ensure(db,hid)
    lv=levels(db,hid);hq=hq_level(db,hid)
    missions=[{"id":r["id"],"key":r["mission_key"],"name":MISSIONS[r["mission_key"]]["name"],"launched_at":r["launched_at"],
               "completes_at":r["completes_at"],"ready":now>=r["completes_at"],"reward":json.loads(r["reward_json"])}
              for r in db.execute("SELECT * FROM ashfall_crystal_frontier_missions WHERE haven_id=? AND claimed_at IS NULL ORDER BY launched_at DESC",(hid,))]
    stats=dict(db.execute("SELECT expeditions_completed,refining_operations FROM ashfall_crystal_frontier_stats WHERE haven_id=?",(hid,)).fetchone())
    earned={r["achievement_key"] for r in db.execute("SELECT achievement_key FROM ashfall_crystal_frontier_achievements WHERE haven_id=?",(hid,))}
    return {"unlocked":hq>=30,"hq_level":hq,"max_level":55,"materials":crystal.balance(db,hid),
            "missions":missions,"mission_catalog":{k:{**v,"unlocked":hq>=v["min_hq"]} for k,v in MISSIONS.items()},
            "research":{k:{**v,"level":lv.get(k,0),"next_cost":research_cost(k,lv.get(k,0)) if lv.get(k,0)<v["max"] else {}} for k,v in RESEARCH.items()},
            "recipes":RECIPES,"achievements":{k:{**v,"earned":k in earned} for k,v in ACHIEVEMENTS.items()},
            "stats":stats,"server_time":now}

def register_crystal_frontier(app,database,get_user,valid_csrf):
    with database() as db:initialize(db)
    def haven(db,user,state):
        row=db.execute("SELECT id FROM ashfall_havens WHERE user_id=? AND state_id=?",(user,state)).fetchone()
        if not row:raise HTTPException(404,"Haven not found")
        return row["id"]
    def user_for(request):
        user=get_user(request.session.get("user_id"))
        if not user:raise HTTPException(401,"Sign in required")
        return user
    @app.get("/ashfall/crystal-frontier")
    async def crystal_frontier_page(request:Request):
        user=get_user(request.session.get("user_id"))
        if not user:return RedirectResponse("/login",status_code=303)
        with database() as db:
            exists=db.execute("SELECT 1 FROM ashfall_havens WHERE user_id=?",(user["id"],)).fetchone()
        if not exists:return RedirectResponse("/ashfall",status_code=303)
        return HTMLResponse((Path(__file__).parent/"ashfall_crystal_frontier.html").read_text(encoding="utf-8"))
    @app.get("/ashfall/api/crystal-frontier")
    async def crystal_frontier_status(request:Request,state_id:int=1):
        user=user_for(request)
        with database() as db:return snapshot(db,haven(db,user["id"],state_id))
    @app.post("/ashfall/api/crystal-frontier/action")
    async def crystal_frontier_action(request:Request):
        user=user_for(request)
        form=await request.form()
        if not valid_csrf(request,str(form.get("csrf_token",""))):raise HTTPException(400,"Invalid security token")
        try:state=int(form.get("state_id","1"))
        except (TypeError,ValueError):raise HTTPException(400,"Invalid state")
        action=str(form.get("action",""))
        with database() as db:
            db.execute("BEGIN IMMEDIATE")
            hid=haven(db,user["id"],state)
            ensure(db,hid)
            try:
                if action=="launch":result=launch(db,hid,str(form.get("key","")))
                elif action=="claim":
                    try:mission_id=int(form.get("mission_id","0"))
                    except (TypeError,ValueError):raise ValueError("Invalid mission ID")
                    result=claim(db,hid,mission_id)
                elif action=="research":result=upgrade_research(db,hid,str(form.get("key","")))
                elif action=="refine":result=refine(db,hid,str(form.get("key","")))
                else:raise ValueError("Unknown action")
            except ValueError as exc:raise HTTPException(409,str(exc))
            return {"result":result,"frontier":snapshot(db,hid)}
