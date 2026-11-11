"""ASHFALL 0.3: server-authoritative First Arrival tutorial and reward ledger."""
import secrets
from datetime import datetime, timezone
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

MISSIONS=(
 {"key":"arrival","title":"A New Beginning","objective":"Enter your Haven","action":"enter","reward":{"food":500,"wood":500}},
 {"key":"headquarters","title":"Secure the Perimeter","objective":"Inspect the Command Center","action":"inspect_hq","reward":{"metal":300}},
 {"key":"scouting","title":"Beyond the Walls","objective":"Open the Wilderness","action":"open_wilderness","reward":{"food":300,"wood":300}},
 {"key":"homecoming","title":"The Way Home","objective":"Return to your settlement","action":"return_settlement","reward":{"gas":150}},
)
NEXT_CHAPTER=("Restore the Farm","Restore the Lumber Yard","Restore the Salvage Station","Restore the Fuel Collector","Upgrade Command Center to Level 2","Complete your first research","Complete your first infected encounter")
RESOURCES=("food","wood","metal","gas")

def initialize(db):
    db.execute("""CREATE TABLE IF NOT EXISTS ashfall_tutorial_progress(
      haven_id INTEGER PRIMARY KEY REFERENCES ashfall_havens(id) ON DELETE CASCADE,
      completed_count INTEGER NOT NULL DEFAULT 0 CHECK(completed_count BETWEEN 0 AND 4),
      updated_at TEXT NOT NULL)""")
    db.execute("""CREATE TABLE IF NOT EXISTS ashfall_resource_balances(
      haven_id INTEGER PRIMARY KEY REFERENCES ashfall_havens(id) ON DELETE CASCADE,
      food INTEGER NOT NULL DEFAULT 0 CHECK(food>=0),
      wood INTEGER NOT NULL DEFAULT 0 CHECK(wood>=0),
      metal INTEGER NOT NULL DEFAULT 0 CHECK(metal>=0),
      gas INTEGER NOT NULL DEFAULT 0 CHECK(gas>=0))""")
    db.execute("""CREATE TABLE IF NOT EXISTS ashfall_tutorial_claims(
      haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
      mission_key TEXT NOT NULL, claimed_at TEXT NOT NULL,
      PRIMARY KEY(haven_id,mission_key))""")

def snapshot(db,haven_id):
    p=db.execute("SELECT completed_count FROM ashfall_tutorial_progress WHERE haven_id=?",(haven_id,)).fetchone()
    balance=db.execute("SELECT food,wood,metal,gas FROM ashfall_resource_balances WHERE haven_id=?",(haven_id,)).fetchone()
    count=p["completed_count"] if p else 0
    return {"completed":count,"total":len(MISSIONS),"mission":MISSIONS[count] if count<len(MISSIONS) else None,
      "resources":dict(balance) if balance else dict.fromkeys(RESOURCES,0),
      "upcoming":[{"title":t,"status":"awaiting gameplay systems"} for t in NEXT_CHAPTER],
      "chapter_complete":count==len(MISSIONS)}

def register_tutorial(app,database,get_user,valid_csrf):
    with database() as db:initialize(db)

    def own_haven(db,user_id,state_id):
        haven=db.execute("SELECT id FROM ashfall_havens WHERE user_id=? AND state_id=?",(user_id,state_id)).fetchone()
        if not haven:raise HTTPException(404,"No Haven in this state")
        return haven["id"]

    @app.get("/ashfall/api/tutorial")
    async def tutorial_status(request:Request,state_id:int=1):
        user=get_user(request.session.get("user_id"))
        if not user:raise HTTPException(401,"Sign in required")
        if not request.session.get("csrf_token"):request.session["csrf_token"]=secrets.token_urlsafe(32)
        with database() as db:
            haven_id=own_haven(db,user["id"],state_id)
            data=snapshot(db,haven_id)
        data["csrf_token"]=request.session["csrf_token"]
        return data

    @app.post("/ashfall/api/tutorial/action")
    async def tutorial_action(request:Request):
        user=get_user(request.session.get("user_id"))
        if not user:raise HTTPException(401,"Sign in required")
        form=await request.form()
        if not valid_csrf(request,str(form.get("csrf_token",""))):raise HTTPException(400,"Invalid security token")
        try:state_id=int(form.get("state_id","1"))
        except (TypeError,ValueError):raise HTTPException(400,"Invalid state")
        action=str(form.get("action",""))[:40]
        if action not in {m["action"] for m in MISSIONS}:raise HTTPException(400,"Invalid tutorial action")
        now=datetime.now(timezone.utc).isoformat()
        with database() as db:
            haven_id=own_haven(db,user["id"],state_id)
            db.execute("INSERT OR IGNORE INTO ashfall_resource_balances(haven_id) VALUES(?)",(haven_id,))
            db.execute("INSERT OR IGNORE INTO ashfall_tutorial_progress(haven_id,updated_at) VALUES(?,?)",(haven_id,now))
            progress=db.execute("SELECT completed_count FROM ashfall_tutorial_progress WHERE haven_id=?",(haven_id,))["completed_count"]
            if progress>=len(MISSIONS) or MISSIONS[progress]["action"]!=action:
                return snapshot(db,haven_id)
            mission=MISSIONS[progress]
            inserted=db.execute("INSERT OR IGNORE INTO ashfall_tutorial_claims(haven_id,mission_key,claimed_at) VALUES(?,?,?)",(haven_id,mission["key"],now))
            if inserted.rowcount==1:
                reward=mission["reward"]
                db.execute("UPDATE ashfall_resource_balances SET food=food+?,wood=wood+?,metal=metal+?,gas=gas+? WHERE haven_id=?",
                  (reward.get("food",0),reward.get("wood",0),reward.get("metal",0),reward.get("gas",0),haven_id))
                db.execute("UPDATE ashfall_tutorial_progress SET completed_count=?,updated_at=? WHERE haven_id=?",(progress+1,now,haven_id))
            result=snapshot(db,haven_id)
            result["claimed"]=mission["title"] if inserted.rowcount==1 else None
        return result
