"""ASHFALL 6.0: server-authoritative hero fragments, ranks, gear and earned caches.

No purchases or randomized paid packs. Rewards are earned through existing events.
"""
import time
from datetime import datetime, timezone
from fastapi import HTTPException, Request
from app.ashfall_heroes import HEROES, hero_level

from app.ashfall_hero_generations import CATALOG,released_generation,is_released,stats
RARITIES={key:hero["rarity"] for key,hero in CATALOG.items()}
RANK_STEPS=(10,20,35,55,80,110,145,185,230,330)
assert sum(RANK_STEPS)==1200
GEAR_TIERS=("BASIC","NORMAL","EPIC","PLATINUM","DIAMOND","LEGENDARY","SUPREME")
GEAR_MATERIALS={
 "BASIC":("scrap",10),"NORMAL":("fabric",18),"EPIC":("alloy",28),
 "PLATINUM":("platinum",40),"DIAMOND":("crystal",55),
 "LEGENDARY":("relic",75),"SUPREME":("core",100)}
SLOTS=("head","body","boots","gloves","weapon","artifact")
SET_BONUSES={3:0.015,6:0.03}

def initialize(db):
 from app.ashfall_hero_mastery import initialize as init_mastery
 init_mastery(db)
 from app.ashfall_hero_operations import initialize as init_operations
 init_operations(db)
 from app.ashfall_hero_collection import initialize as init_collection
 init_collection(db)
 # Shared hero assignment table is also used by the original hero module.
 # Creating it here makes initialization safe for standalone databases/tests.
 db.execute("""CREATE TABLE IF NOT EXISTS ashfall_hero_assignments(
  haven_id INTEGER PRIMARY KEY REFERENCES ashfall_havens(id) ON DELETE CASCADE,
  hero_key TEXT NOT NULL)""")
 db.execute("""CREATE TABLE IF NOT EXISTS ashfall_hero_fragments(
  haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
  hero_key TEXT NOT NULL,quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity>=0),
  PRIMARY KEY(haven_id,hero_key))""")
 db.execute("""CREATE TABLE IF NOT EXISTS ashfall_hero_ranks(
  haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
  hero_key TEXT NOT NULL,rank INTEGER NOT NULL DEFAULT 0 CHECK(rank BETWEEN 0 AND 10),
  PRIMARY KEY(haven_id,hero_key))""")
 db.execute("""CREATE TABLE IF NOT EXISTS ashfall_hero_materials(
  haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
  material TEXT NOT NULL,quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity>=0),
  PRIMARY KEY(haven_id,material))""")
 db.execute("""CREATE TABLE IF NOT EXISTS ashfall_hero_gear(
  haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
  hero_key TEXT NOT NULL,slot TEXT NOT NULL,tier INTEGER NOT NULL CHECK(tier BETWEEN 0 AND 6),
  PRIMARY KEY(haven_id,hero_key,slot))""")
 db.execute("""CREATE TABLE IF NOT EXISTS ashfall_hero_reward_claims(
  haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
  period TEXT NOT NULL,kind TEXT NOT NULL,claimed_at REAL NOT NULL,
  PRIMARY KEY(haven_id,period,kind))""")

def grant(db,hid,material,amount):
 if amount<=0:raise ValueError("Positive reward required")
 db.execute("""INSERT INTO ashfall_hero_materials(haven_id,material,quantity)
 VALUES(?,?,?) ON CONFLICT(haven_id,material) DO UPDATE SET quantity=quantity+excluded.quantity""",
 (hid,material,amount))

def grant_fragments(db,hid,key,amount):
 if key not in HEROES or amount<=0:raise ValueError("Invalid fragment grant")
 db.execute("""INSERT INTO ashfall_hero_fragments(haven_id,hero_key,quantity)
 VALUES(?,?,?) ON CONFLICT(haven_id,hero_key) DO UPDATE SET quantity=quantity+excluded.quantity""",
 (hid,key,amount))

def consume(db,hid,material,amount):
 row=db.execute("""UPDATE ashfall_hero_materials SET quantity=quantity-?
 WHERE haven_id=? AND material=? AND quantity>=?""",(amount,hid,material,amount))
 if row.rowcount!=1:raise HTTPException(409,"Insufficient "+material)

def consume_fragments(db,hid,key,amount):
 row=db.execute("""UPDATE ashfall_hero_fragments SET quantity=quantity-?
 WHERE haven_id=? AND hero_key=? AND quantity>=?""",(amount,hid,key,amount))
 if row.rowcount!=1:raise HTTPException(409,"Insufficient hero fragments")

def roster(db,hid):
 owned={r["hero_key"]:r["xp"] for r in db.execute(
  "SELECT hero_key,xp FROM ashfall_heroes WHERE haven_id=?",(hid,))}
 fragments={r["hero_key"]:r["quantity"] for r in db.execute(
  "SELECT hero_key,quantity FROM ashfall_hero_fragments WHERE haven_id=?",(hid,))}
 ranks={r["hero_key"]:r["rank"] for r in db.execute(
  "SELECT hero_key,rank FROM ashfall_hero_ranks WHERE haven_id=?",(hid,))}
 materials={r["material"]:r["quantity"] for r in db.execute(
  "SELECT material,quantity FROM ashfall_hero_materials WHERE haven_id=?",(hid,))}
 gear={(r["hero_key"],r["slot"]):r["tier"] for r in db.execute(
  "SELECT hero_key,slot,tier FROM ashfall_hero_gear WHERE haven_id=?",(hid,))}
 from app.ashfall_hero_mastery import skill_snapshot
 from app.ashfall_hero_warfare import snapshot as warfare_snapshot
 from app.ashfall_hero_collection import snapshot as collection_snapshot
 result=[]
 for key,definition in HEROES.items():
  rank=ranks.get(key,0)
  skills=skill_snapshot(db,hid,key,materials)
  equipment={slot:GEAR_TIERS[gear[(key,slot)]] if (key,slot) in gear else None for slot in SLOTS}
  result.append({"key":key,"name":definition["name"],"title":definition["title"],
   "generation":CATALOG[key]["generation"],"released":is_released(db,hid,key),
   "stats":stats(key,hero_level(owned[key]) if key in owned else 0,rank,equipment,skills),
   "specialty":definition["specialty"],"rarity":RARITIES.get(key,"NORMAL"),
   "owned":key in owned,"level":hero_level(owned.get(key,0)) if key in owned else 0,
   "rank":rank,"max_rank":len(RANK_STEPS),
   "fragments":fragments.get(key,0),
   "skills":skills,
   "next_rank_cost":RANK_STEPS[rank] if rank<len(RANK_STEPS) else None,
   "gear":equipment,
   "warfare":warfare_snapshot(db,hid,key),
   "gear_set_count":sum(v is not None for v in equipment.values()),
   "gear_set_bonus_percent":sum(v*100 for count,v in SET_BONUSES.items() if sum(x is not None for x in equipment.values())>=count),
   "power":(100+hero_level(owned[key])*20+rank*125+
     sum((gear.get((key,slot),-1)+1)*55 for slot in SLOTS)) if key in owned else 0})
 assignment=db.execute("SELECT hero_key FROM ashfall_hero_assignments WHERE haven_id=?",(hid,)).fetchone()
 weekly_claims=db.execute("SELECT COUNT(*) FROM ashfall_hero_reward_claims WHERE haven_id=? AND kind='weekly'",(hid,)).fetchone()[0]
 return {"weekly_claims":weekly_claims,
  "weekly_claims_until_next_generation":max(0,2-weekly_claims%2) if released_generation(db,hid)<16 else 0,
  "released_generation":released_generation(db,hid),"total_generations":16,
  "generation_size":10,"total_heroes":160,
  "assigned":assignment[0] if assignment else None,"heroes":result,"materials":materials,"gear_tiers":GEAR_TIERS,
  "rank_total_fragments":sum(RANK_STEPS),"unlock_fragments":10,
  "rank_steps":RANK_STEPS,"gear_materials":GEAR_MATERIALS,
  "collection":collection_snapshot(db,hid)}

def progress(db,hid,key,action,slot=None):
 if key not in HEROES:raise HTTPException(400,"Unknown hero")
 if not is_released(db,hid,key):raise HTTPException(409,"Hero generation not yet released")
 owned=db.execute("SELECT 1 FROM ashfall_heroes WHERE haven_id=? AND hero_key=?",(hid,key)).fetchone()
 if action=="unlock":
  if owned:raise HTTPException(409,"Hero already unlocked")
  consume_fragments(db,hid,key,10)
  db.execute("INSERT INTO ashfall_heroes(haven_id,hero_key,xp,recruited_at) VALUES(?,?,0,?)",
             (hid,key,time.time()))
 elif action=="rank":
  if not owned:raise HTTPException(409,"Unlock hero first")
  row=db.execute("SELECT rank FROM ashfall_hero_ranks WHERE haven_id=? AND hero_key=?",(hid,key)).fetchone()
  rank=row["rank"] if row else 0
  if rank>=len(RANK_STEPS):raise HTTPException(409,"Maximum rank")
  consume_fragments(db,hid,key,RANK_STEPS[rank])
  db.execute("""INSERT INTO ashfall_hero_ranks(haven_id,hero_key,rank) VALUES(?,?,?)
  ON CONFLICT(haven_id,hero_key) DO UPDATE SET rank=excluded.rank""",(hid,key,rank+1))
 elif action=="craft":
  if not owned:raise HTTPException(409,"Unlock hero first")
  if slot not in SLOTS:raise HTTPException(400,"Invalid equipment slot")
  row=db.execute("SELECT tier FROM ashfall_hero_gear WHERE haven_id=? AND hero_key=? AND slot=?",
                 (hid,key,slot)).fetchone()
  tier=row["tier"]+1 if row else 0
  if tier>=len(GEAR_TIERS):raise HTTPException(409,"Maximum equipment tier")
  material,amount=GEAR_MATERIALS[GEAR_TIERS[tier]]
  consume(db,hid,material,amount)
  db.execute("""INSERT INTO ashfall_hero_gear(haven_id,hero_key,slot,tier) VALUES(?,?,?,?)
  ON CONFLICT(haven_id,hero_key,slot) DO UPDATE SET tier=excluded.tier""",
  (hid,key,slot,tier))
 else:raise HTTPException(400,"Invalid hero action")

def reward_period(now,kind):
 dt=datetime.fromtimestamp(now,timezone.utc)
 return dt.strftime("%Y-%m-%d") if kind=="daily" else f"{dt.isocalendar().year}-W{dt.isocalendar().week:02d}"

def claim_reward(db,hid,kind,now):
 if kind not in ("daily","weekly"):raise HTTPException(400,"Invalid reward")
 period=reward_period(now,kind)
 row=db.execute("""INSERT OR IGNORE INTO ashfall_hero_reward_claims
 (haven_id,period,kind,claimed_at) VALUES(?,?,?,?)""",(hid,period,kind,now))
 if row.rowcount!=1:raise HTTPException(409,"Reward already claimed")
 if kind=="daily":
  grant_fragments(db,hid,"mara",3)
  grant(db,hid,"scrap",12);grant(db,hid,"fabric",5);grant(db,hid,"gold_fragment",1)
  grant(db,hid,"training_manual",4)
  from app.ashfall_hero_generations import CATALOG,released_generation
  generation=released_generation(db,hid)
  key=next(k for k,v in CATALOG.items() if v["generation"]==generation)
  grant_fragments(db,hid,key,1)
 else:
  grant_fragments(db,hid,"kael",12);grant_fragments(db,hid,"nyra",5);grant_fragments(db,hid,"orion",2)
  grant(db,hid,"alloy",35);grant(db,hid,"platinum",18)
  grant(db,hid,"crystal",12);grant(db,hid,"gold_fragment",8)
  grant(db,hid,"training_manual",18);grant(db,hid,"skill_insignia",6)
  from app.ashfall_hero_generations import CATALOG,released_generation
  generation=released_generation(db,hid)
  for key,hero in CATALOG.items():
   if hero["generation"]==generation:grant_fragments(db,hid,key,2)
 return {"period":period,"kind":kind}

def register_hero_ascension(app,database,get_user,valid_csrf):
 with database() as db:initialize(db)
 def owner(db,request,state):
  user=get_user(request.session.get("user_id"))
  if not user:raise HTTPException(401,"Sign in required")
  row=db.execute("SELECT id FROM ashfall_havens WHERE user_id=? AND state_id=?",
                 (user["id"],state)).fetchone()
  if not row:raise HTTPException(404,"Haven not found")
  return row["id"]
 @app.get("/ashfall/api/hero-ascension")
 async def get_roster(request:Request,state_id:int=1):
  with database() as db:
   hid=owner(db,request,state_id)
   data=roster(db,hid)
   now=time.time()
   from app.ashfall_hero_operations import status as operation_status
   data["operations"]=operation_status(db,hid,now)
   data["reward_status"]={kind:bool(db.execute("""SELECT 1 FROM ashfall_hero_reward_claims
     WHERE haven_id=? AND period=? AND kind=?""",
     (hid,reward_period(now,kind),kind)).fetchone()) for kind in ("daily","weekly")}
   return data
 @app.post("/ashfall/api/hero-ascension/action")
 async def hero_progress(request:Request):
  form=await request.form()
  if not valid_csrf(request,str(form.get("csrf_token",""))):
   raise HTTPException(400,"Invalid security token")
  try:state=int(form.get("state_id","1"))
  except (ValueError,TypeError):raise HTTPException(400,"Invalid state")
  action=str(form.get("action",""))
  with database() as db:
   db.execute("BEGIN IMMEDIATE")
   hid=owner(db,request,state)
   if action=="collection":
    from app.ashfall_hero_collection import claim as claim_collection
    result={"rewards":claim_collection(db,hid,str(form.get("milestone","")),time.time())}
   elif action=="operation":
    from app.ashfall_hero_operations import claim as claim_operation
    result={"rewards":claim_operation(db,hid,str(form.get("operation","")),time.time())}
   elif action=="reward":
    result=claim_reward(db,hid,str(form.get("kind","")),time.time())
   elif action=="train":
    from app.ashfall_hero_mastery import train
    try:index=int(form.get("skill_index","-1"))
    except (ValueError,TypeError):raise HTTPException(400,"Invalid skill")
    result={"skill_level":train(db,hid,str(form.get("hero","")),index)}
   elif action=="assign":
    key=str(form.get("hero",""))
    if key not in HEROES:raise HTTPException(400,"Unknown hero")
    if not db.execute("SELECT 1 FROM ashfall_heroes WHERE haven_id=? AND hero_key=?",(hid,key)).fetchone():
     raise HTTPException(409,"Unlock hero first")
    db.execute("""INSERT INTO ashfall_hero_assignments(haven_id,hero_key) VALUES(?,?)
      ON CONFLICT(haven_id) DO UPDATE SET hero_key=excluded.hero_key""",(hid,key))
    result={"assigned":key}
   elif action=="exchange":
    key=str(form.get("hero",""))
    if key not in HEROES:raise HTTPException(400,"Unknown hero")
    if not is_released(db,hid,key):raise HTTPException(409,"Hero generation not yet released")
    # A predictable exchange; no random loot or paid currency.
    rate={"NORMAL":1,"EPIC":2,"LEGENDARY":4,"SUPREME":8}[RARITIES[key]]
    consume(db,hid,"gold_fragment",rate)
    grant_fragments(db,hid,key,1)
    result={"exchanged_for":key,"gold_cost":rate}
   else:
    progress(db,hid,str(form.get("hero","")),action,str(form.get("slot","")))
    result={"action":action,"hero":str(form.get("hero",""))}
   updated=roster(db,hid)
   from app.ashfall_hero_operations import status as operation_status
   updated["operations"]=operation_status(db,hid,time.time())
   updated["reward_status"]={kind:bool(db.execute("""SELECT 1 FROM ashfall_hero_reward_claims
     WHERE haven_id=? AND period=? AND kind=?""",(hid,reward_period(time.time(),kind),kind)).fetchone()) for kind in ("daily","weekly")}
   return {"result":result,"roster":updated}
