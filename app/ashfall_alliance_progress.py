"""ASHFALL 1.8 — cooperative alliance contributions and claim-once objectives."""
import time
from datetime import datetime, timezone
from fastapi import HTTPException, Request
from app.ashfall_economy import snapshot as economy_snapshot
from app.ashfall_chapter import level_for

RESOURCES=("food","wood","metal","gas")
PROJECTS=(
 ("supply_network","Supply Network","food",1500,{"wood":250,"metal":100},350),
 ("fortification","Fortify the Frontier","wood",1200,{"food":250,"metal":150},400),
 ("salvage_drive","Salvage Initiative","metal",800,{"food":350,"gas":60},450),
 ("fuel_reserve","Emergency Fuel Reserve","gas",400,{"wood":350,"metal":150},500),
)
def initialize(db):
 db.execute("""CREATE TABLE IF NOT EXISTS ashfall_alliance_projects(
 alliance_id INTEGER NOT NULL REFERENCES ashfall_alliances(id) ON DELETE CASCADE,
 project_key TEXT NOT NULL,contributed INTEGER NOT NULL DEFAULT 0 CHECK(contributed>=0),
 completed_at REAL,PRIMARY KEY(alliance_id,project_key))""")
 db.execute("""CREATE TABLE IF NOT EXISTS ashfall_alliance_contributions(
 id INTEGER PRIMARY KEY AUTOINCREMENT,alliance_id INTEGER NOT NULL REFERENCES ashfall_alliances(id) ON DELETE CASCADE,
 haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id),project_key TEXT NOT NULL,
 resource TEXT NOT NULL,amount INTEGER NOT NULL,created_at REAL NOT NULL)""")
 db.execute("""CREATE TABLE IF NOT EXISTS ashfall_alliance_project_claims(
 alliance_id INTEGER NOT NULL REFERENCES ashfall_alliances(id) ON DELETE CASCADE,
 haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id),
 project_key TEXT NOT NULL,claimed_at REAL NOT NULL,
 PRIMARY KEY(alliance_id,haven_id,project_key))""")
 db.execute("""CREATE TABLE IF NOT EXISTS ashfall_alliance_progress(
 alliance_id INTEGER PRIMARY KEY REFERENCES ashfall_alliances(id) ON DELETE CASCADE,
 xp INTEGER NOT NULL DEFAULT 0 CHECK(xp>=0))""")
 db.execute("CREATE INDEX IF NOT EXISTS idx_ashfall_contribution_haven ON ashfall_alliance_contributions(alliance_id,haven_id)")

def snapshot(db,hid,state,now):
 membership=db.execute("""SELECT m.alliance_id FROM ashfall_alliance_members m
 JOIN ashfall_alliances a ON a.id=m.alliance_id WHERE m.haven_id=? AND a.state_id=?""",(hid,state)).fetchone()
 if not membership:return {"member":False,"projects":[]}
 aid=membership["alliance_id"]
 row=db.execute("SELECT xp FROM ashfall_alliance_progress WHERE alliance_id=?",(aid,)).fetchone()
 xp=row["xp"] if row else 0
 claimed={r["project_key"] for r in db.execute("SELECT project_key FROM ashfall_alliance_project_claims WHERE alliance_id=? AND haven_id=?",(aid,hid))}
 contributions={r["project_key"]:r["amount"] for r in db.execute("""SELECT project_key,SUM(amount) AS amount FROM ashfall_alliance_contributions
 WHERE alliance_id=? AND haven_id=? GROUP BY project_key""",(aid,hid))}
 rows={r["project_key"]:dict(r) for r in db.execute("SELECT project_key,contributed,completed_at FROM ashfall_alliance_projects WHERE alliance_id=?",(aid,))}
 projects=[]
 for key,name,resource,goal,reward,bonus_xp in PROJECTS:
  progress=rows.get(key,{})
  projects.append({"key":key,"name":name,"resource":resource,"goal":goal,
   "contributed":progress.get("contributed",0),"completed":progress.get("completed_at") is not None,
   "my_contribution":contributions.get(key,0),"claimed":key in claimed,
   "reward":reward,"xp_reward":bonus_xp})
 econ=economy_snapshot(db,hid,now)
 return {"member":True,"alliance_id":aid,"xp":xp,"level":level_for(xp),
  "next_level_xp":100*level_for(xp)*(level_for(xp)+1)//2 if level_for(xp)<100 else None,
  "projects":projects,"resources":econ["resources"]}

def register_alliance_progress(app,database,get_user,valid_csrf):
 with database() as db:initialize(db)
 def own(db,uid,state):
  row=db.execute("SELECT id FROM ashfall_havens WHERE user_id=? AND state_id=?",(uid,state)).fetchone()
  if not row:raise HTTPException(404,"Haven not found")
  return row["id"]
 @app.get("/ashfall/api/alliance-progress")
 async def status(request:Request,state_id:int=1):
  user=get_user(request.session.get("user_id"))
  if not user:raise HTTPException(401,"Sign in required")
  with database() as db:return snapshot(db,own(db,user["id"],state_id),state_id,time.time())
 @app.post("/ashfall/api/alliance-progress/action")
 async def action(request:Request):
  user=get_user(request.session.get("user_id"))
  if not user:raise HTTPException(401,"Sign in required")
  form=await request.form()
  if not valid_csrf(request,str(form.get("csrf_token",""))):raise HTTPException(400,"Security token invalid")
  try:state=int(form.get("state_id","1"))
  except (TypeError,ValueError):raise HTTPException(400,"Invalid State")
  command=str(form.get("action",""))
  key=str(form.get("project",""))
  project=next((p for p in PROJECTS if p[0]==key),None)
  if command not in ("contribute","claim") or not project:raise HTTPException(400,"Invalid project action")
  now=time.time()
  with database() as db:
   hid=own(db,user["id"],state)
   current=snapshot(db,hid,state,now)
   if not current["member"]:raise HTTPException(403,"Join an alliance first")
   aid=current["alliance_id"]
   target=next(p for p in current["projects"] if p["key"]==key)
   _,_,resource,goal,reward,bonus_xp=project
   if command=="contribute":
    try:amount=int(form.get("amount","0"))
    except (TypeError,ValueError):raise HTTPException(400,"Invalid amount")
    if amount<1 or amount>10000:raise HTTPException(400,"Contribution must be between 1 and 10000")
    if target["completed"]:raise HTTPException(409,"Project already complete")
    if amount>goal-target["contributed"]:raise HTTPException(409,"Contribution exceeds remaining project goal")
    db.execute("INSERT OR IGNORE INTO ashfall_alliance_projects(alliance_id,project_key,contributed) VALUES(?,?,0)",(aid,key))
    debit=db.execute(f"UPDATE ashfall_resource_balances SET {resource}={resource}-? WHERE haven_id=? AND {resource}>=?",(amount,hid,amount))
    if debit.rowcount!=1:raise HTTPException(409,"Not enough resources")
    db.execute("INSERT INTO ashfall_alliance_contributions(alliance_id,haven_id,project_key,resource,amount,created_at) VALUES(?,?,?,?,?,?)",(aid,hid,key,resource,amount,now))
    db.execute("UPDATE ashfall_alliance_projects SET contributed=contributed+? WHERE alliance_id=? AND project_key=?",(amount,aid,key))
    if target["contributed"]+amount==goal:
     db.execute("UPDATE ashfall_alliance_projects SET completed_at=? WHERE alliance_id=? AND project_key=?",(now,aid,key))
     db.execute("INSERT OR IGNORE INTO ashfall_alliance_progress(alliance_id,xp) VALUES(?,0)",(aid,))
     db.execute("UPDATE ashfall_alliance_progress SET xp=xp+? WHERE alliance_id=?",(bonus_xp,aid))
   else:
    if not target["completed"]:raise HTTPException(409,"Project not complete")
    if target["my_contribution"]<=0:raise HTTPException(403,"Contribute to the project to earn its reward")
    inserted=db.execute("INSERT OR IGNORE INTO ashfall_alliance_project_claims(alliance_id,haven_id,project_key,claimed_at) VALUES(?,?,?,?)",(aid,hid,key,now))
    if inserted.rowcount!=1:raise HTTPException(409,"Reward already claimed")
    db.execute("UPDATE ashfall_resource_balances SET food=food+?,wood=wood+?,metal=metal+?,gas=gas+? WHERE haven_id=?",
     (*(reward.get(r,0) for r in RESOURCES),hid))
    db.execute("INSERT OR IGNORE INTO ashfall_haven_progression(haven_id,xp) VALUES(?,0)",(hid,))
    db.execute("UPDATE ashfall_haven_progression SET xp=xp+? WHERE haven_id=?",(bonus_xp,hid))
   return snapshot(db,hid,state,now)
