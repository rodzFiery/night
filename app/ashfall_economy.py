"""ASHFALL 0.4: authoritative offline production and timed construction."""
import time
import math
from fastapi import HTTPException, Request
from app.ashfall_tutorial import initialize as init_balances
from app.ashfall_alliance_technology import production_bonus
from app import ashfall_crystal_age as crystal

BUILDINGS={
 "farm":{"name":"Farm","resource":"food","rate":120,"cost":{"wood":120,"metal":30},"seconds":45},
 "lumber":{"name":"Lumber Yard","resource":"wood","rate":100,"cost":{"food":120,"metal":30},"seconds":45},
 "salvage":{"name":"Salvage Station","resource":"metal","rate":80,"cost":{"food":150,"wood":120},"seconds":60},
 "fuel":{"name":"Fuel Collector","resource":"gas","rate":25,"cost":{"food":180,"wood":140,"metal":70},"seconds":90},
 "barracks":{"name":"Barracks","resource":None,"rate":0,"cost":{"food":180,"wood":220,"metal":90},"seconds":90},
 "hq":{"name":"Command Center","resource":None,"rate":0,"cost":{"food":350,"wood":350,"metal":150,"gas":50},"seconds":120},
}
RES=("food","wood","metal","gas")
# ASHFALL 44 — Haven economic doctrine: one persistent focus per Haven.
# Focus boosts exactly one conventional resource by 8%; changes have a 24h cooldown.
DOCTRINES={"balanced":None,"agriculture":"food","forestry":"wood","industry":"metal","energy":"gas"}
DOCTRINE_BONUS=0.08
DOCTRINE_COOLDOWN=86400
# ASHFALL 46: mastery is earned through elapsed active specialization time.
# Five ranks, each requiring 24 hours of focused Haven production.
MASTERY_STEP_SECONDS=86400
MASTERY_MAX_RANK=5
MASTERY_BONUS_PER_RANK=0.01

def mastery_rank(seconds):
    return min(MASTERY_MAX_RANK,max(0,int(seconds//MASTERY_STEP_SECONDS)))

def mastery_status(db,haven_id):
    rows=db.execute("SELECT focus,active_seconds FROM ashfall_doctrine_mastery WHERE haven_id=?",(haven_id,)).fetchall()
    totals={row["focus"]:float(row["active_seconds"]) for row in rows}
    return {focus:{"active_seconds":round(totals.get(focus,0),2),
                   "rank":mastery_rank(totals.get(focus,0)),
                   "production_bonus":MASTERY_BONUS_PER_RANK*mastery_rank(totals.get(focus,0)),
                   "next_rank_seconds":min(MASTERY_MAX_RANK,mastery_rank(totals.get(focus,0))+1)*MASTERY_STEP_SECONDS}
            for focus in DOCTRINES if focus!="balanced"}


def doctrine_status(db,haven_id,now):
    row=db.execute("SELECT focus,changed_at FROM ashfall_economic_doctrine WHERE haven_id=?",(haven_id,)).fetchone()
    focus=row["focus"] if row and row["focus"] in DOCTRINES else "balanced"
    changed=float(row["changed_at"]) if row else 0.0
    return {"focus":focus,"resource":DOCTRINES[focus],"bonus":DOCTRINE_BONUS if DOCTRINES[focus] else 0,
            "can_change":not row or now>=changed+DOCTRINE_COOLDOWN,
            "next_change_at":max(0,changed+DOCTRINE_COOLDOWN) if row else 0}


def production_per_hour(base_rate,level,research_level=0,alliance_bonus=0,doctrine_bonus=0):
    """Server-authoritative production multiplier; returns zero for unbuilt facilities."""
    if level<=0:return 0.0
    return (base_rate*(1.18**(level-1))*(1+0.1*research_level)
            *(1+alliance_bonus)*(1+doctrine_bonus))

def production_interval(rate_per_hour,seconds,fraction):
    """Carry fractional resources forward across arbitrary offline time intervals."""
    amount=max(0.0,seconds)*rate_per_hour/3600+fraction
    rounded=round(amount)
    if math.isclose(amount,rounded,rel_tol=0,abs_tol=1e-9):
        amount=float(rounded)
    whole=math.floor(amount)
    return whole,amount-whole

def initialize(db):
    init_balances(db)
    db.execute("""CREATE TABLE IF NOT EXISTS ashfall_building_levels(
      haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
      building_key TEXT NOT NULL, level INTEGER NOT NULL DEFAULT 0 CHECK(level BETWEEN 0 AND 55),
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
    db.execute("""CREATE TABLE IF NOT EXISTS ashfall_economic_doctrine(
      haven_id INTEGER PRIMARY KEY REFERENCES ashfall_havens(id) ON DELETE CASCADE,
      focus TEXT NOT NULL DEFAULT 'balanced'
        CHECK(focus IN ('balanced','agriculture','forestry','industry','energy')),
      changed_at REAL NOT NULL DEFAULT 0)""")
    db.execute("""CREATE TABLE IF NOT EXISTS ashfall_doctrine_mastery(
      haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
      focus TEXT NOT NULL CHECK(focus IN ('agriculture','forestry','industry','energy')),
      active_seconds REAL NOT NULL DEFAULT 0 CHECK(active_seconds>=0),
      PRIMARY KEY(haven_id,focus))""")
    crystal.initialize(db)

def prepare(db,haven_id,now):
    db.execute("INSERT OR IGNORE INTO ashfall_resource_balances(haven_id) VALUES(?)",(haven_id,))
    db.execute("INSERT OR IGNORE INTO ashfall_economy_clock(haven_id,last_tick) VALUES(?,?)",(haven_id,now))
    crystal.prepare(db,haven_id)
    for key in BUILDINGS:
        db.execute("INSERT OR IGNORE INTO ashfall_building_levels(haven_id,building_key,level) VALUES(?,?,?)",
                   (haven_id,key,1 if key=="hq" else 0))

def accrue(db,haven_id,now):
    prepare(db,haven_id,now)
    clock=db.execute("SELECT * FROM ashfall_economy_clock WHERE haven_id=?",(haven_id,)).fetchone()
    # Never rewind the accrual cursor: clock corrections must not mint resources.
    last_tick=float(clock["last_tick"])
    start=min(now,last_tick)
    if now<last_tick:
        return
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
    doctrine=doctrine_status(db,haven_id,now)
    focused_resource=doctrine["resource"]
    # A facility may finish construction during offline accrual, so eligibility
    # is checked per interval rather than only at the start of the whole tick.
    focused_key=doctrine["focus"] if focused_resource else None
    mastery=mastery_status(db,haven_id)
    focus_seconds=mastery[focused_key]["active_seconds"] if focused_key else 0.0
    def interval(seconds):
        nonlocal focus_seconds
        if seconds<=0:return
        remaining=seconds
        operational=bool(focused_key and any(
            definition["resource"]==focused_resource and levels[key]>0
            for key,definition in BUILDINGS.items()))
        while remaining>0:
            rank=mastery_rank(focus_seconds) if operational else 0
            until_next=(rank+1)*MASTERY_STEP_SECONDS-focus_seconds if operational and rank<MASTERY_MAX_RANK else remaining
            segment=min(remaining,max(0.000001,until_next))
            for key,definition in BUILDINGS.items():
                resource=definition["resource"]
                if resource and levels[key]:
                    doctrine_bonus=(DOCTRINE_BONUS+rank*MASTERY_BONUS_PER_RANK) if resource==focused_resource else 0
                    rate=production_per_hour(
                        definition["rate"],levels[key],
                        research_levels.get(resource_tech[resource],0),
                        alliance_bonuses[resource],doctrine_bonus)
                    whole,part=production_interval(rate,segment,fractions[resource])
                    gains[resource]+=whole
                    fractions[resource]=part
            if operational:focus_seconds+=segment
            remaining-=segment
    boundaries=[(now,"end",None)]
    # Overdue queues may predate the current clock after a crash or migration.
    # Complete them immediately at the cursor, never silently strand them.
    if queue and queue["finishes_at"]<=now:
        boundaries.append((max(start,queue["finishes_at"]),"building",queue))
    if research_queue and research_queue["finishes_at"]<=now:
        boundaries.append((max(start,research_queue["finishes_at"]),"research",research_queue))
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
    if focused_key:
        db.execute("""INSERT INTO ashfall_doctrine_mastery(haven_id,focus,active_seconds)
                      VALUES(?,?,?) ON CONFLICT(haven_id,focus) DO UPDATE
                      SET active_seconds=excluded.active_seconds""",
                   (haven_id,focused_key,focus_seconds))
    db.execute("""UPDATE ashfall_economy_clock SET last_tick=?,food_fraction=?,wood_fraction=?,metal_fraction=?,gas_fraction=? WHERE haven_id=?""",
               (now,*(fractions[r] for r in RES),haven_id))

def production_breakdown(db,haven_id,levels,now):
    """Authoritative current hourly rates, including all earned modifiers.

    This is an informational forecast of the *current* configuration, not
    a promise about future construction, research, or doctrine changes.
    """
    doctrine=doctrine_status(db,haven_id,now)
    mastery=mastery_status(db,haven_id)
    try:
        research={row["tech_key"]:row["level"] for row in
                  db.execute("SELECT tech_key,level FROM ashfall_technology WHERE haven_id=?",(haven_id,))}
    except Exception:
        research={}
    tech={"food":"agriculture","wood":"forestry","metal":"metallurgy","gas":"fuel_processing"}
    result={}
    for key,definition in BUILDINGS.items():
        resource=definition["resource"]
        if not resource:
            continue
        level=int(levels.get(key,0))
        focused=resource==doctrine["resource"]
        mastery_rank_now=mastery.get(doctrine["focus"],{}).get("rank",0) if focused else 0
        specialization=(DOCTRINE_BONUS+mastery_rank_now*MASTERY_BONUS_PER_RANK) if focused else 0
        alliance=production_bonus(db,haven_id,resource)
        research_level=int(research.get(tech[resource],0))
        rate=production_per_hour(definition["rate"],level,research_level,alliance,specialization)
        result[resource]={
            "facility":key,
            "level":level,
            "per_hour":round(rate,2),
            "research_level":research_level,
            "alliance_bonus":round(alliance,6),
            "doctrine_bonus":round(specialization,6),
        }
    return result


def snapshot(db,haven_id,now):
    accrue(db,haven_id,now)
    levels={r["building_key"]:r["level"] for r in db.execute("SELECT * FROM ashfall_building_levels WHERE haven_id=?",(haven_id,))}
    balances=dict(db.execute("SELECT food,wood,metal,gas FROM ashfall_resource_balances WHERE haven_id=?",(haven_id,)).fetchone())
    queue=db.execute("SELECT building_key,target_level,finishes_at FROM ashfall_construction_queue WHERE haven_id=?",(haven_id,)).fetchone()
    buildings={}
    for key,definition in BUILDINGS.items():
        level=levels[key]
        next_level=level+1
        costs=crystal.conventional_cost(definition["cost"],level,1 if key=="hq" else 0)
        if level>=crystal.NORMAL_CAP:
            # Crystal architecture research provides an earned rare-material discount.
            try:
                row=db.execute("SELECT level FROM ashfall_crystal_frontier_research WHERE haven_id=? AND tech_key='prismatic_architecture'",(haven_id,)).fetchone()
                architecture=int(row["level"]) if row else 0
            except Exception:
                architecture=0
            rare_cost=crystal.crystal_cost(level)
            rare_cost={k:max(1,int(math.ceil(v*(1-.03*architecture)))) if v else 0 for k,v in rare_cost.items()}
        else:
            rare_cost={}
        seconds=crystal.construction_seconds(definition["seconds"],level,1 if key=="hq" else 0)
        buildings[key]={"name":definition["name"],"level":level,"next_level":next_level,
                        "cost":costs,"seconds":seconds,"rate":round(definition["rate"]*1.18**(level-1),1) if level and definition["resource"] else 0,
                        "resource":definition["resource"],"unlocked":key=="hq" or levels["hq"]>=1,
                        "era":crystal.stage(level)["era"],"crystal_level":max(0,level-30),
                        "rare_cost":rare_cost,"max_level":crystal.MAX_LEVEL}
    return {"production_rates":production_breakdown(db,haven_id,levels,now), "doctrine":doctrine_status(db,haven_id,now), "mastery":mastery_status(db,haven_id), "resources":balances,"rare_materials":crystal.balance(db,haven_id),
            "buildings":buildings,"queue":dict(queue) if queue else None,"server_time":now}

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
            # Snapshot accrues resources and advances persistent clocks. Serialize
            # the read-modify-write cycle so simultaneous polls cannot double-credit.
            db.execute("BEGIN IMMEDIATE")
            return snapshot(db,haven(db,user["id"],state_id),time.time())

    @app.post("/ashfall/api/economy/doctrine")
    async def economy_doctrine(request:Request):
        user=get_user(request.session.get("user_id"))
        if not user:raise HTTPException(401,"Sign in required")
        form=await request.form()
        if not valid_csrf(request,str(form.get("csrf_token",""))):
            raise HTTPException(400,"Invalid security token")
        focus=str(form.get("focus",""))
        if focus not in DOCTRINES:raise HTTPException(400,"Unknown economic doctrine")
        try:state=int(form.get("state_id","1"))
        except (ValueError,TypeError):raise HTTPException(400,"Invalid state")
        now=time.time()
        with database() as db:
            db.execute("BEGIN IMMEDIATE")
            hid=haven(db,user["id"],state)
            # Credit all elapsed production under the old doctrine before switching.
            accrue(db,hid,now)
            current=doctrine_status(db,hid,now)
            if current["focus"]==focus:return snapshot(db,hid,now)
            if not current["can_change"]:
                raise HTTPException(409,"Economic doctrine is on cooldown")
            db.execute("""INSERT INTO ashfall_economic_doctrine(haven_id,focus,changed_at)
                          VALUES(?,?,?) ON CONFLICT(haven_id) DO UPDATE
                          SET focus=excluded.focus,changed_at=excluded.changed_at""",
                       (hid,focus,now))
            return snapshot(db,hid,now)

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
            # Serialize upgrades before reading balances and the construction slot.
            # Otherwise two concurrent requests can both pass the same checks.
            db.execute("BEGIN IMMEDIATE")
            hid=haven(db,user["id"],state)
            data=snapshot(db,hid,now)
            if data["queue"]:raise HTTPException(409,"Construction slot occupied")
            building=data["buildings"][key]
            if building["level"]>=crystal.MAX_LEVEL:raise HTTPException(409,"Maximum level reached")
            if building["level"]>=30 and data["buildings"]["hq"]["level"]<30:
                raise HTTPException(409,"Crystal Age requires Command Center level 30")
            if not building["unlocked"]:raise HTTPException(409,"Building locked")
            if key!="hq" and building["next_level"]>data["buildings"]["hq"]["level"]:
                raise HTTPException(409,"Upgrade Command Center first")
            if key=="hq" and building["level"]>=2 and any(data["buildings"][k]["level"]<building["level"]-1 for k in ("farm","lumber","salvage","fuel")):
                raise HTTPException(409,"Develop production buildings first")
            cost=building["cost"]
            if any(data["resources"][r]<v for r,v in cost.items()):
                raise HTTPException(409,"Insufficient resources")
            rare=building["rare_cost"]
            if any(data["rare_materials"][k]<v for k,v in rare.items()):
                raise HTTPException(409,"Insufficient Crystal Age materials")
            if rare:
                db.execute("UPDATE ashfall_crystal_balances SET crystal_shards=crystal_shards-?,ancient_cores=ancient_cores-?,prismatic_essence=prismatic_essence-? WHERE haven_id=?",
                    (rare["crystal_shards"],rare["ancient_cores"],rare["prismatic_essence"],hid))
            db.execute("UPDATE ashfall_resource_balances SET food=food-?,wood=wood-?,metal=metal-?,gas=gas-? WHERE haven_id=?",
                       (*(cost.get(r,0) for r in RES),hid))
            db.execute("INSERT INTO ashfall_construction_queue(haven_id,building_key,target_level,finishes_at) VALUES(?,?,?,?)",
                       (hid,key,building["next_level"],now+building["seconds"]))
            return snapshot(db,hid,now)

    @app.post("/ashfall/api/economy/crystal-salvage")
    async def crystal_salvage(request:Request):
        user=get_user(request.session.get("user_id"))
        if not user:raise HTTPException(401,"Sign in required")
        form=await request.form()
        if not valid_csrf(request,str(form.get("csrf_token",""))):
            raise HTTPException(400,"Invalid security token")
        try:state=int(form.get("state_id","1"))
        except (ValueError,TypeError):raise HTTPException(400,"Invalid state")
        with database() as db:
            db.execute("BEGIN IMMEDIATE")
            hid=haven(db,user["id"],state)
            accrue(db,hid,time.time())
            try:reward=crystal.salvage(db,hid)
            except ValueError as exc:raise HTTPException(409,str(exc))
            return {"reward":reward,"rare_materials":crystal.balance(db,hid)}
