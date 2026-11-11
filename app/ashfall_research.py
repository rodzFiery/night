"""ASHFALL 0.6: persistent timed research and real production modifiers."""
import time
from fastapi import HTTPException, Request
from app.ashfall_economy import snapshot as economy_snapshot

TECH={
 "agriculture":{"name":"Resilient Agriculture","description":"Increase Farm production by 10% per level.","resource":"food","cost":{"food":180,"wood":150,"metal":50},"seconds":75,"requires_hq":2},
 "forestry":{"name":"Salvage Logistics","description":"Increase Lumber Yard production by 10% per level.","resource":"wood","cost":{"food":200,"wood":180,"metal":80},"seconds":90,"requires_hq":2},
 "metallurgy":{"name":"Scrap Refinement","description":"Increase Metal production by 10% per level.","resource":"metal","cost":{"food":240,"wood":200,"metal":100},"seconds":120,"requires_hq":3},
 "fuel_processing":{"name":"Fuel Processing","description":"Increase Gas production by 10% per level.","resource":"gas","cost":{"food":280,"wood":240,"metal":120,"gas":40},"seconds":150,"requires_hq":3},
}
RES=("food","wood","metal","gas")

def initialize(db):
    db.execute("""CREATE TABLE IF NOT EXISTS ashfall_technology(
      haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
      tech_key TEXT NOT NULL, level INTEGER NOT NULL DEFAULT 0 CHECK(level BETWEEN 0 AND 10),
      PRIMARY KEY(haven_id,tech_key))""")
    db.execute("""CREATE TABLE IF NOT EXISTS ashfall_research_queue(
      haven_id INTEGER PRIMARY KEY REFERENCES ashfall_havens(id) ON DELETE CASCADE,
      tech_key TEXT NOT NULL, target_level INTEGER NOT NULL, finishes_at REAL NOT NULL)""")

def complete(db,hid,now):
    queue=db.execute("SELECT * FROM ashfall_research_queue WHERE haven_id=?",(hid,)).fetchone()
    if queue and queue["finishes_at"]<=now:
        db.execute("INSERT OR IGNORE INTO ashfall_technology(haven_id,tech_key,level) VALUES(?,?,0)",(hid,queue["tech_key"]))
        db.execute("UPDATE ashfall_technology SET level=? WHERE haven_id=? AND tech_key=?",(queue["target_level"],hid,queue["tech_key"]))
        db.execute("DELETE FROM ashfall_research_queue WHERE haven_id=?",(hid,))

def levels(db,hid):
    return {r["tech_key"]:r["level"] for r in db.execute("SELECT tech_key,level FROM ashfall_technology WHERE haven_id=?",(hid,))}

def snapshot(db,hid,now):
    econ=economy_snapshot(db,hid,now)
    complete(db,hid,now)
    current=levels(db,hid)
    queue=db.execute("SELECT tech_key,target_level,finishes_at FROM ashfall_research_queue WHERE haven_id=?",(hid,)).fetchone()
    hq=econ["buildings"]["hq"]["level"]
    techs={}
    for key,tech in TECH.items():
        level=current.get(key,0)
        mult=1.65**level
        techs[key]={"name":tech["name"],"description":tech["description"],"level":level,
          "max_level":10,"unlocked":hq>=tech["requires_hq"],"requires_hq":tech["requires_hq"],
          "cost":{r:int(v*mult) for r,v in tech["cost"].items()},
          "seconds":int(tech["seconds"]*(1.5**level)),
          "bonus_percent":10*level}
    return {"technologies":techs,"queue":dict(queue) if queue else None,"server_time":now,"resources":econ["resources"],"hq_level":hq}

def register_research(app,database,get_user,valid_csrf):
    with database() as db:initialize(db)
    def own(db,user,state):
        row=db.execute("SELECT id FROM ashfall_havens WHERE user_id=? AND state_id=?",(user,state)).fetchone()
        if not row:raise HTTPException(404,"Haven not found")
        return row["id"]

    @app.get("/ashfall/api/research")
    async def research_status(request:Request,state_id:int=1):
        user=get_user(request.session.get("user_id"))
        if not user:raise HTTPException(401,"Sign in required")
        with database() as db:return snapshot(db,own(db,user["id"],state_id),time.time())

    @app.post("/ashfall/api/research/start")
    async def start_research(request:Request):
        user=get_user(request.session.get("user_id"))
        if not user:raise HTTPException(401,"Sign in required")
        form=await request.form()
        if not valid_csrf(request,str(form.get("csrf_token",""))):raise HTTPException(400,"Invalid security token")
        key=str(form.get("technology",""))
        if key not in TECH:raise HTTPException(400,"Unknown technology")
        try:state=int(form.get("state_id","1"))
        except (ValueError,TypeError):raise HTTPException(400,"Invalid state")
        now=time.time()
        with database() as db:
            hid=own(db,user["id"],state)
            result=snapshot(db,hid,now)
            tech=result["technologies"][key]
            if result["queue"]:raise HTTPException(409,"Research slot occupied")
            if not tech["unlocked"]:raise HTTPException(409,"Upgrade Command Center to level "+str(tech["requires_hq"])+" first")
            if tech["level"]>=tech["max_level"]:raise HTTPException(409,"Maximum research level reached")
            if any(result["resources"][r]<v for r,v in tech["cost"].items()):raise HTTPException(409,"Insufficient resources")
            db.execute("UPDATE ashfall_resource_balances SET food=food-?,wood=wood-?,metal=metal-?,gas=gas-? WHERE haven_id=?",
                       (*(tech["cost"].get(r,0) for r in RES),hid))
            db.execute("INSERT INTO ashfall_research_queue(haven_id,tech_key,target_level,finishes_at) VALUES(?,?,?,?)",
                       (hid,key,tech["level"]+1,now+tech["seconds"]))
            return snapshot(db,hid,now)
