"""ASHFALL 0.4: authoritative offline production and timed construction."""
import time
from fastapi import HTTPException, Request
from app.ashfall_tutorial import initialize as init_balances
from app.ashfall_alliance_technology import production_bonus

BUILDINGS={
 "farm":{"name":"Farm","resource":"food","rate":120,"cost":{"wood":120,"metal":30},"seconds":45},
 "lumber":{"name":"Lumber Yard","resource":"wood","rate":100,"cost":{"food":120,"metal":30},"seconds":45},
 "salvage":{"name":"Salvage Station","resource":"metal","rate":80,"cost":{"food":150,"wood":120},"seconds":60},
 "fuel":{"name":"Fuel Collector","resource":"gas","rate":25,"cost":{"food":180,"wood":140,"metal":70},"seconds":90},
 "barracks":{"name":"Barracks","resource":None,"rate":0,"cost":{"food":180,"wood":220,"metal":90},"seconds":90},
 "hq":{"name":"Command Center","resource":None,"rate":0,"cost":{"food":350,"wood":350,"metal":150,"gas":50},"seconds":120},
}
RES=("food","wood","metal","gas")

def initialize(db):
    init_balances(db)
    db.execute("""CREATE TABLE IF NOT EXISTS ashfall_building_levels(
      haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
      building_key TEXT NOT NULL, level INTEGER NOT NULL DEFAULT 0 CHECK(level BETWEEN 0 AND 30),
      PRIMARY KEY(haven_id,building_key))""")
    db.execute("""CREATE TABLE IF NOT EXISTS ashfall_construction_queue(
      haven_id INTEGER PRIMARY KEY REFERENCES ashfall_havens(id) ON DELETE CASCADE,
      building_key TEXT NOT NULL, target_level INTEGER NOT NULL,
      finishes_at REAL NOT NULL)""")
    db.execute("""CREATE TABLE IF NOT EXISTS ashfall_economy_clock(
      haven_id INTEGER PRIMARY KEY REFERENCES ashfall_havens(id) ON DELETE CASCADE,
      last_tick REAL NOT NULL, food_fraction REAL NOT NULL DEFAULT 0,
      wood_fraction REAL NOT NULL DEFAULT 0,metal_fraction REAL NOT NULL DEFAULT 0,
      gas_fraction REAL NOT NULL DEFAULT 0)""")

def prepare(db,haven_id,now):
    db.execute("INSERT OR IGNORE INTO ashfall_resource_balances(haven_id) VALUES(?)",(haven_id,))
    db.execute("INSERT OR IGNORE INTO ashfall_economy_clock(haven_id,last_tick) VALUES(?,?)",(haven_id,now))
    for key in BUILDINGS:
        db.execute("INSERT OR IGNORE INTO ashfall_building_levels(haven_id,building_key,level) VALUES(?,?,?)",
                   (haven_id,key,1 if key=="hq" else 0))

def accrue(db,haven_id,now):
    prepare(db,haven_id,now)
    clock=db.execute("SELECT * FROM ashfall_economy_clock WHERE haven_id=?",(haven_id,)).fetchone()
    start=min(now,float(clock["last_tick"]))
    queue=db.execute("SELECT * FROM ashfall_construction_queue WHERE haven_id=?",(haven_id,)).fetchone()
    levels={r["building_key"]:r["level"] for r in db.execute("SELECT * FROM ashfall_building_levels WHERE haven_id=?",(haven_id,))}
    fractions={r:float(clock[r+"_fraction"]) for r in RES}
    gains={r:0 for r in RES}
    try:
        research_levels={r["tech_key"]:r["level"] for r in db.execute("SELECT tech_key,level FROM ashfall_technology WHERE haven_id=?",(haven_id,))}
        research_queue=db.execute("SELECT tech_key,target_level,finishes_at FROM ashfall_research_queue WHERE haven_id=?",(haven_id,)).fetchone()
    except Exception:
        research_levels={}
        research_queue=None
    resource_tech={"food":"agriculture","wood":"forestry","metal":"metallurgy","gas":"fuel_processing"}
    alliance_bonuses={resource:production_bonus(db,haven_id,resource) for resource in RES}
    def interval(seconds):
        if seconds<=0:return
        for key,definition in BUILDINGS.items():
            resource=definition["resource"]
            if resource and levels[key]:
                amount=seconds*definition["rate"]*(1.18**(levels[key]-1))*(1+0.1*research_levels.get(resource_tech[resource],0))*(1+alliance_bonuses[resource])/3600+fractions[resource]
                whole=int(amount)
                gains[resource]+=whole
                fractions[resource]=amount-whole
    boundaries=[(now,"end",None)]
    if queue and start<queue["finishes_at"]<=now:boundaries.append((queue["finishes_at"],"building",queue))
    if research_queue and start<research_queue["finishes_at"]<=now:boundaries.append((research_queue["finishes_at"],"research",research_queue))
    boundaries.sort(key=lambda item:item[0])
    cursor=start
    for boundary,kind,event in boundaries:
        interval(max(0,boundary-cursor))
        cursor=boundary
        if kind=="building":
            levels[event["building_key"]]=event["target_level"]
            db.execute("UPDATE ashfall_building_levels SET level=? WHERE haven_id=? AND building_key=?",
                       (event["target_level"],haven_id,event["building_key"]))
            if event["building_key"]=="hq":
                db.execute("UPDATE ashfall_havens SET command_center_level=? WHERE id=?",(event["target_level"],haven_id))
            db.execute("DELETE FROM ashfall_construction_queue WHERE haven_id=?",(haven_id,))
        elif kind=="research":
            research_levels[event["tech_key"]]=event["target_level"]
            db.execute("INSERT OR IGNORE INTO ashfall_technology(haven_id,tech_key,level) VALUES(?,?,0)",(haven_id,event["tech_key"]))
            db.execute("UPDATE ashfall_technology SET level=? WHERE haven_id=? AND tech_key=?",(event["target_level"],haven_id,event["tech_key"]))
            db.execute("DELETE FROM ashfall_research_queue WHERE haven_id=?",(haven_id,))
    db.execute("""UPDATE ashfall_resource_balances SET food=food+?,wood=wood+?,metal=metal+?,gas=gas+? WHERE haven_id=?""",
               (*(gains[r] for r in RES),haven_id))
    db.execute("""UPDATE ashfall_economy_clock SET last_tick=?,food_fraction=?,wood_fraction=?,metal_fraction=?,gas_fraction=? WHERE haven_id=?""",
               (now,*(fractions[r] for r in RES),haven_id))

def snapshot(db,haven_id,now):
    accrue(db,haven_id,now)
    levels={r["building_key"]:r["level"] for r in db.execute("SELECT * FROM ashfall_building_levels WHERE haven_id=?",(haven_id,))}
    balances=dict(db.execute("SELECT food,wood,metal,gas FROM ashfall_resource_balances WHERE haven_id=?",(haven_id,)).fetchone())
    queue=db.execute("SELECT building_key,target_level,finishes_at FROM ashfall_construction_queue WHERE haven_id=?",(haven_id,)).fetchone()
    buildings={}
    for key,definition in BUILDINGS.items():
        level=levels[key]
        next_level=level+1
        multiplier=1.6**max(0,level-(1 if key=="hq" else 0))
        costs={r:int(v*multiplier) for r,v in definition["cost"].items()}
        seconds=int(definition["seconds"]*(1.45**max(0,level-(1 if key=="hq" else 0))))
        buildings[key]={"name":definition["name"],"level":level,"next_level":next_level,
                        "cost":costs,"seconds":seconds,"rate":round(definition["rate"]*1.18**(level-1),1) if level and definition["resource"] else 0,
                        "resource":definition["resource"],"unlocked":key=="hq" or levels["hq"]>=1}
    return {"resources":balances,"buildings":buildings,"queue":dict(queue) if queue else None,"server_time":now}

def register_economy(app,database,get_user,valid_csrf):
    with database() as db:initialize(db)
    def haven(db,user,state):
        row=db.execute("SELECT id FROM ashfall_havens WHERE user_id=? AND state_id=?",(user,state)).fetchone()
        if not row:raise HTTPException(404,"Haven not found")
        return row["id"]

    @app.get("/ashfall/api/economy")
    async def economy_status(request:Request,state_id:int=1):
        user=get_user(request.session.get("user_id"))
        if not user:raise HTTPException(401,"Sign in required")
        with database() as db:
            return snapshot(db,haven(db,user["id"],state_id),time.time())

    @app.post("/ashfall/api/economy/upgrade")
    async def economy_upgrade(request:Request):
        user=get_user(request.session.get("user_id"))
        if not user:raise HTTPException(401,"Sign in required")
        form=await request.form()
        if not valid_csrf(request,str(form.get("csrf_token",""))):raise HTTPException(400,"Invalid security token")
        key=str(form.get("building",""))
        if key not in BUILDINGS:raise HTTPException(400,"Unknown building")
        try:state=int(form.get("state_id","1"))
        except ValueError:raise HTTPException(400,"Invalid state")
        now=time.time()
        with database() as db:
            hid=haven(db,user["id"],state)
            data=snapshot(db,hid,now)
            if data["queue"]:raise HTTPException(409,"Construction slot occupied")
            building=data["buildings"][key]
            if building["level"]>=30:raise HTTPException(409,"Maximum level reached")
            if not building["unlocked"]:raise HTTPException(409,"Building locked")
            if key!="hq" and building["next_level"]>data["buildings"]["hq"]["level"]:
                raise HTTPException(409,"Upgrade Command Center first")
            if key=="hq" and building["level"]>=2 and any(data["buildings"][k]["level"]<building["level"]-1 for k in ("farm","lumber","salvage","fuel")):
                raise HTTPException(409,"Develop production buildings first")
            cost=building["cost"]
            if any(data["resources"][r]<v for r,v in cost.items()):
                raise HTTPException(409,"Insufficient resources")
            db.execute("UPDATE ashfall_resource_balances SET food=food-?,wood=wood-?,metal=metal-?,gas=gas-? WHERE haven_id=?",
                       (*(cost.get(r,0) for r in RES),hid))
            db.execute("INSERT INTO ashfall_construction_queue(haven_id,building_key,target_level,finishes_at) VALUES(?,?,?,?)",
                       (hid,key,building["next_level"],now+building["seconds"]))
            return snapshot(db,hid,now)
