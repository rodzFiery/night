"""ASHFALL 1.9 — alliance technology unlocks and contribution rankings."""
from fastapi import HTTPException, Request
from app.ashfall_chapter import level_for

TECHS=(
 ("agronomy","Collective Agronomy","food","supply_network"),
 ("forestry","Frontier Forestry","wood","fortification"),
 ("recycling","Salvage Engineering","metal","salvage_drive"),
 ("refining","Fuel Refinement","gas","fuel_reserve"),
)
LEVELS=(2,4,6)
def membership(db,hid):
 try:
  return db.execute("""SELECT m.alliance_id FROM ashfall_alliance_members m
  WHERE m.haven_id=?""",(hid,)).fetchone()
 except Exception:return None

def technology(db,hid):
 member=membership(db,hid)
 if not member:return {"member":False,"level":0,"xp":0,"techs":[],"leaderboard":[],"my_total":0}
 aid=member["alliance_id"]
 row=db.execute("SELECT xp FROM ashfall_alliance_progress WHERE alliance_id=?",(aid,)).fetchone()
 xp=row["xp"] if row else 0
 level=level_for(xp)
 completed={r["project_key"] for r in db.execute("""SELECT project_key FROM ashfall_alliance_projects
 WHERE alliance_id=? AND completed_at IS NOT NULL""",(aid,))}
 techs=[]
 for key,name,resource,prereq in TECHS:
  unlocked=sum(level>=threshold for threshold in LEVELS) if prereq in completed else 0
  techs.append({"key":key,"name":name,"resource":resource,"level":unlocked,"max_level":3,
   "bonus_percent":unlocked*5,"required_project":prereq,"project_complete":prereq in completed,
   "next_level_required":LEVELS[unlocked] if unlocked<3 else None})
 leaderboard=[dict(r) for r in db.execute("""SELECT h.name AS haven_name,h.id AS haven_id,
  SUM(c.amount) AS total,COUNT(*) AS contributions
  FROM ashfall_alliance_contributions c JOIN ashfall_havens h ON h.id=c.haven_id
  WHERE c.alliance_id=? GROUP BY c.haven_id ORDER BY total DESC,h.name LIMIT 20""",(aid,))]
 own=db.execute("SELECT COALESCE(SUM(amount),0) AS total FROM ashfall_alliance_contributions WHERE alliance_id=? AND haven_id=?",(aid,hid)).fetchone()
 return {"member":True,"level":level,"xp":xp,"techs":techs,"leaderboard":leaderboard,"my_total":own["total"]}

def production_bonus(db,hid,resource):
 # Read-only lookup; no economy import or recursion.
 try:
  member=membership(db,hid)
  if not member:return 0.0
  aid=member["alliance_id"]
  row=db.execute("SELECT xp FROM ashfall_alliance_progress WHERE alliance_id=?",(aid,)).fetchone()
  if not row:return 0.0
  level=level_for(row["xp"])
  tech=next((t for t in TECHS if t[2]==resource),None)
  if not tech:return 0.0
  done=db.execute("SELECT 1 FROM ashfall_alliance_projects WHERE alliance_id=? AND project_key=? AND completed_at IS NOT NULL",(aid,tech[3])).fetchone()
  return .05*sum(level>=threshold for threshold in LEVELS) if done else 0.0
 except Exception:return 0.0

def register_alliance_technology(app,database,get_user):
 @app.get("/ashfall/api/alliance-technology")
 async def status(request:Request,state_id:int=1):
  user=get_user(request.session.get("user_id"))
  if not user:raise HTTPException(401,"Sign in required")
  with database() as db:
   haven=db.execute("SELECT id FROM ashfall_havens WHERE user_id=? AND state_id=?",(user["id"],state_id)).fetchone()
   if not haven:raise HTTPException(404,"Haven not found")
   return technology(db,haven["id"])
