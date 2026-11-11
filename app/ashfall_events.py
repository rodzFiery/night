"""ASHFALL 1.5: daily world events and one-time discoveries, server-authoritative rewards."""
import hashlib
import time
from datetime import datetime, timezone
from fastapi import HTTPException, Request
from app.ashfall_economy import snapshot as economy_snapshot

RES=("food","wood","metal","gas")
EVENTS=(
 ("supply_drop","Fallen Supply Convoy","Recover emergency supplies from a damaged convoy.",{"food":130,"wood":100},65),
 ("signal","Distress Signal","Investigate a survivor radio transmission.",{"metal":85,"food":90},80),
 ("storm","After the Ash Storm","Search the debris field after a passing storm.",{"wood":110,"gas":30},95),
 ("cache","Forgotten Reserve","Open a sealed pre-fall supply reserve.",{"food":100,"metal":95},75),
 ("relay","Silent Relay","Restore contact with a distant communications relay.",{"wood":125,"metal":75},90),
)
DISCOVERIES=(
 ("observatory","Collapsed Observatory","Locate a forgotten observation post.",{"metal":110},100),
 ("station","Old Ranger Station","Chart a former ranger outpost.",{"wood":130},100),
 ("bunker","Buried Shelter","Map an abandoned underground shelter.",{"food":150},120),
)
def initialize(db):
 db.execute("""CREATE TABLE IF NOT EXISTS ashfall_event_claims(
   haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
   event_day TEXT NOT NULL,event_key TEXT NOT NULL,claimed_at REAL NOT NULL,
   PRIMARY KEY(haven_id,event_day,event_key))""")
 db.execute("""CREATE TABLE IF NOT EXISTS ashfall_discoveries(
   haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
   discovery_key TEXT NOT NULL,discovered_at REAL NOT NULL,
   PRIMARY KEY(haven_id,discovery_key))""")

def day_key(now):return datetime.fromtimestamp(now,timezone.utc).strftime("%Y-%m-%d")
def coords(hid,key):
 digest=hashlib.sha256(f"ashfall:exploration:{hid}:{key}".encode()).digest()
 return int.from_bytes(digest[:2],"big")%35-17,int.from_bytes(digest[2:4],"big")%35-17

def todays_events(now):
 day=day_key(now)
 order=sorted(EVENTS,key=lambda item:hashlib.sha256(f"{day}:{item[0]}".encode()).digest())
 return order[:3]

def snapshot(db,hid,now):
 econ=economy_snapshot(db,hid,now)
 day=day_key(now)
 claimed={r["event_key"] for r in db.execute("SELECT event_key FROM ashfall_event_claims WHERE haven_id=? AND event_day=?",(hid,day))}
 found={r["discovery_key"] for r in db.execute("SELECT discovery_key FROM ashfall_discoveries WHERE haven_id=?",(hid,))}
 events=[]
 for key,name,description,reward,xp in todays_events(now):
  x,y=coords(hid,key)
  events.append({"key":key,"name":name,"description":description,"x":x,"y":y,"reward":reward,"xp":xp,"claimed":key in claimed})
 discoveries=[]
 for key,name,description,reward,xp in DISCOVERIES:
  x,y=coords(hid,key)
  discoveries.append({"key":key,"name":name,"description":description,"x":x,"y":y,"reward":reward,"xp":xp,"discovered":key in found})
 return {"day":day,"server_time":now,"events":events,"discoveries":discoveries,"resources":econ["resources"],
         "next_reset_at":(int(now//86400)+1)*86400}

def register_events(app,database,get_user,valid_csrf):
 with database() as db:initialize(db)
 def own(db,uid,state):
  row=db.execute("SELECT id FROM ashfall_havens WHERE user_id=? AND state_id=?",(uid,state)).fetchone()
  if not row:raise HTTPException(404,"Haven not found")
  return row["id"]

 @app.get("/ashfall/api/events")
 async def event_status(request:Request,state_id:int=1):
  user=get_user(request.session.get("user_id"))
  if not user:raise HTTPException(401,"Sign in required")
  with database() as db:return snapshot(db,own(db,user["id"],state_id),time.time())

 @app.post("/ashfall/api/events/claim")
 async def claim_event(request:Request):
  user=get_user(request.session.get("user_id"))
  if not user:raise HTTPException(401,"Sign in required")
  form=await request.form()
  if not valid_csrf(request,str(form.get("csrf_token",""))):raise HTTPException(400,"Invalid security token")
  kind=str(form.get("kind",""));key=str(form.get("key",""))
  try:state=int(form.get("state_id","1"))
  except (ValueError,TypeError):raise HTTPException(400,"Invalid state")
  if kind not in ("event","discovery"):raise HTTPException(400,"Invalid action")
  now=time.time()
  with database() as db:
   db.execute("BEGIN IMMEDIATE")
   hid=own(db,user["id"],state)
   current=snapshot(db,hid,now)
   options=current["events"] if kind=="event" else current["discoveries"]
   target=next((item for item in options if item["key"]==key),None)
   if not target:raise HTTPException(404,"Location unavailable")
   if target["claimed" if kind=="event" else "discovered"]:raise HTTPException(409,"Already completed")
   if kind=="event":
    inserted=db.execute("INSERT OR IGNORE INTO ashfall_event_claims(haven_id,event_day,event_key,claimed_at) VALUES(?,?,?,?)",(hid,current["day"],key,now))
   else:
    inserted=db.execute("INSERT OR IGNORE INTO ashfall_discoveries(haven_id,discovery_key,discovered_at) VALUES(?,?,?)",(hid,key,now))
   if inserted.rowcount!=1:raise HTTPException(409,"Reward already claimed")
   reward=target["reward"]
   db.execute("UPDATE ashfall_resource_balances SET food=food+?,wood=wood+?,metal=metal+?,gas=gas+? WHERE haven_id=?",
              (*(reward.get(r,0) for r in RES),hid))
   db.execute("INSERT OR IGNORE INTO ashfall_haven_progression(haven_id,xp) VALUES(?,0)",(hid,))
   db.execute("UPDATE ashfall_haven_progression SET xp=xp+? WHERE haven_id=?",(target["xp"],hid))
   return snapshot(db,hid,now)
