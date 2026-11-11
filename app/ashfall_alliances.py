"""ASHFALL 1.6 — state-scoped alliances, membership and invitations."""
import re
import time
from fastapi import HTTPException, Request

def initialize(db):
 db.execute("""CREATE TABLE IF NOT EXISTS ashfall_alliances(
 id INTEGER PRIMARY KEY AUTOINCREMENT,state_id INTEGER NOT NULL REFERENCES ashfall_states(id),
 name TEXT NOT NULL COLLATE NOCASE,tag TEXT NOT NULL COLLATE NOCASE,
 description TEXT NOT NULL DEFAULT '',leader_haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id),
 created_at REAL NOT NULL,UNIQUE(state_id,name),UNIQUE(state_id,tag))""")
 db.execute("""CREATE TABLE IF NOT EXISTS ashfall_alliance_members(
 haven_id INTEGER PRIMARY KEY REFERENCES ashfall_havens(id) ON DELETE CASCADE,
 alliance_id INTEGER NOT NULL REFERENCES ashfall_alliances(id) ON DELETE CASCADE,
 role TEXT NOT NULL CHECK(role IN ('leader','member')),joined_at REAL NOT NULL)""")
 db.execute("""CREATE TABLE IF NOT EXISTS ashfall_alliance_invites(
 id INTEGER PRIMARY KEY AUTOINCREMENT,alliance_id INTEGER NOT NULL REFERENCES ashfall_alliances(id) ON DELETE CASCADE,
 target_haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
 invited_by INTEGER NOT NULL REFERENCES ashfall_havens(id),created_at REAL NOT NULL,
 UNIQUE(alliance_id,target_haven_id))""")

def snapshot(db,hid,state):
 membership=db.execute("SELECT alliance_id,role FROM ashfall_alliance_members WHERE haven_id=?",(hid,)).fetchone()
 invites=[dict(r) for r in db.execute("""SELECT i.id,a.name,a.tag,i.alliance_id FROM ashfall_alliance_invites i
 JOIN ashfall_alliances a ON a.id=i.alliance_id WHERE i.target_haven_id=? AND a.state_id=? ORDER BY i.id DESC""",(hid,state))]
 alliances=[dict(r) for r in db.execute("""SELECT a.id,a.name,a.tag,a.description,
 (SELECT COUNT(*) FROM ashfall_alliance_members m WHERE m.alliance_id=a.id) AS member_count
 FROM ashfall_alliances a WHERE a.state_id=? ORDER BY member_count DESC,a.id LIMIT 50""",(state,))]
 mine=None
 if membership:
  row=db.execute("SELECT id,name,tag,description,leader_haven_id FROM ashfall_alliances WHERE id=?",(membership["alliance_id"],)).fetchone()
  if row:
   mine=dict(row);mine["role"]=membership["role"]
   mine["members"]=[dict(r) for r in db.execute("""SELECT h.id AS haven_id,h.name,m.role,h.command_center_level AS hq
   FROM ashfall_alliance_members m JOIN ashfall_havens h ON h.id=m.haven_id
   WHERE m.alliance_id=? ORDER BY CASE m.role WHEN 'leader' THEN 0 ELSE 1 END,h.name""",(row["id"],))]
 return {"mine":mine,"invites":invites,"alliances":alliances}

def register_alliances(app,database,get_user,valid_csrf):
 with database() as db:initialize(db)
 def own(db,uid,state):
  row=db.execute("SELECT id FROM ashfall_havens WHERE user_id=? AND state_id=?",(uid,state)).fetchone()
  if not row:raise HTTPException(404,"Haven not found in State")
  return row["id"]
 @app.get("/ashfall/api/alliances")
 async def alliance_status(request:Request,state_id:int=1):
  user=get_user(request.session.get("user_id"))
  if not user:raise HTTPException(401,"Sign in required")
  with database() as db:return snapshot(db,own(db,user["id"],state_id),state_id)
 @app.post("/ashfall/api/alliances/action")
 async def alliance_action(request:Request):
  user=get_user(request.session.get("user_id"))
  if not user:raise HTTPException(401,"Sign in required")
  form=await request.form()
  if not valid_csrf(request,str(form.get("csrf_token",""))):raise HTTPException(400,"Invalid security token")
  action=str(form.get("action",""))
  try:state=int(form.get("state_id","1"))
  except (TypeError,ValueError):raise HTTPException(400,"Invalid State")
  if action not in ("create","invite","accept","decline","leave","disband"):raise HTTPException(400,"Unknown action")
  now=time.time()
  with database() as db:
   hid=own(db,user["id"],state)
   member=db.execute("SELECT alliance_id,role FROM ashfall_alliance_members WHERE haven_id=?",(hid,)).fetchone()
   if action=="create":
    name=str(form.get("name","")).strip();tag=str(form.get("tag","")).strip().upper()
    if not 3<=len(name)<=32 or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 _-]*",name):raise HTTPException(400,"Name must be 3–32 letters, numbers, spaces, hyphens or underscores")
    if not re.fullmatch(r"[A-Z0-9]{2,5}",tag):raise HTTPException(400,"Tag must be 2–5 letters or numbers")
    if member:raise HTTPException(409,"Leave your alliance first")
    if db.execute("SELECT 1 FROM ashfall_alliances WHERE state_id=? AND (name=? OR tag=?)",(state,name,tag)).fetchone():raise HTTPException(409,"Alliance name or tag taken")
    cursor=db.execute("INSERT INTO ashfall_alliances(state_id,name,tag,leader_haven_id,created_at) VALUES(?,?,?,?,?)",(state,name,tag,hid,now))
    db.execute("INSERT INTO ashfall_alliance_members(haven_id,alliance_id,role,joined_at) VALUES(?,?,'leader',?)",(hid,cursor.lastrowid,now))
   elif action=="invite":
    if not member or member["role"]!="leader":raise HTTPException(403,"Only alliance leaders can invite")
    target_name=str(form.get("haven_name","")).strip()
    target=db.execute("SELECT id FROM ashfall_havens WHERE state_id=? AND name=? COLLATE NOCASE",(state,target_name)).fetchone()
    if not target or target["id"]==hid:raise HTTPException(404,"Other Haven not found in this State")
    if db.execute("SELECT 1 FROM ashfall_alliance_members WHERE haven_id=?",(target["id"],)).fetchone():raise HTTPException(409,"Haven already belongs to an alliance")
    db.execute("INSERT OR IGNORE INTO ashfall_alliance_invites(alliance_id,target_haven_id,invited_by,created_at) VALUES(?,?,?,?)",(member["alliance_id"],target["id"],hid,now))
   elif action in ("accept","decline"):
    try:invite_id=int(form.get("invite_id","0"))
    except (ValueError,TypeError):raise HTTPException(400,"Invalid invitation")
    invitation=db.execute("""SELECT i.id,i.alliance_id FROM ashfall_alliance_invites i JOIN ashfall_alliances a ON a.id=i.alliance_id
      WHERE i.id=? AND i.target_haven_id=? AND a.state_id=?""",(invite_id,hid,state)).fetchone()
    if not invitation:raise HTTPException(404,"Invitation not found")
    if action=="accept":
     if member:raise HTTPException(409,"Already in an alliance")
     db.execute("INSERT INTO ashfall_alliance_members(haven_id,alliance_id,role,joined_at) VALUES(?,?,'member',?)",(hid,invitation["alliance_id"],now))
    db.execute("DELETE FROM ashfall_alliance_invites WHERE id=?",(invite_id,))
    if action=="accept":db.execute("DELETE FROM ashfall_alliance_invites WHERE target_haven_id=?",(hid,))
   elif action=="leave":
    if not member:raise HTTPException(409,"Not in an alliance")
    if member["role"]=="leader":raise HTTPException(409,"Leader must disband the alliance (leadership transfer not yet available)")
    db.execute("DELETE FROM ashfall_alliance_members WHERE haven_id=?",(hid,))
   elif action=="disband":
    if not member or member["role"]!="leader":raise HTTPException(403,"Only alliance leaders can disband")
    db.execute("DELETE FROM ashfall_alliances WHERE id=? AND state_id=?",(member["alliance_id"],state))
   return snapshot(db,hid,state)
