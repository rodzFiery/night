"""ASHFALL 0.7 — persistent troop recruitment, training queue and military roster."""
import time
from fastapi import HTTPException, Request
from app.ashfall_economy import snapshot as economy_snapshot

UNITS={
 "infantry":{"name":"Infantry","role":"Frontline defense","cost":{"food":5,"wood":3},"seconds":4,"hq":1},
 "rider":{"name":"Riders","role":"Fast mobile troops","cost":{"food":6,"metal":4},"seconds":5,"hq":2},
 "hunter":{"name":"Hunters","role":"Ranged damage","cost":{"food":5,"wood":2,"metal":3},"seconds":6,"hq":3},
}
RES=("food","wood","metal","gas")
def initialize(db):
    db.execute("""CREATE TABLE IF NOT EXISTS ashfall_troops(
      haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
      unit_key TEXT NOT NULL, quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity>=0),
      PRIMARY KEY(haven_id,unit_key))""")
    db.execute("""CREATE TABLE IF NOT EXISTS ashfall_training_queue(
      haven_id INTEGER PRIMARY KEY REFERENCES ashfall_havens(id) ON DELETE CASCADE,
      unit_key TEXT NOT NULL, quantity INTEGER NOT NULL CHECK(quantity>0),
      finishes_at REAL NOT NULL)""")

def settle(db,hid,now):
    queue=db.execute("SELECT unit_key,quantity,finishes_at FROM ashfall_training_queue WHERE haven_id=?",(hid,)).fetchone()
    if queue and queue["finishes_at"]<=now:
        db.execute("INSERT OR IGNORE INTO ashfall_troops(haven_id,unit_key,quantity) VALUES(?,?,0)",(hid,queue["unit_key"]))
        db.execute("UPDATE ashfall_troops SET quantity=quantity+? WHERE haven_id=? AND unit_key=?",(queue["quantity"],hid,queue["unit_key"]))
        db.execute("DELETE FROM ashfall_training_queue WHERE haven_id=?",(hid,))

def snapshot(db,hid,now):
    econ=economy_snapshot(db,hid,now)
    settle(db,hid,now)
    roster={r["unit_key"]:r["quantity"] for r in db.execute("SELECT unit_key,quantity FROM ashfall_troops WHERE haven_id=?",(hid,))}
    queue=db.execute("SELECT unit_key,quantity,finishes_at FROM ashfall_training_queue WHERE haven_id=?",(hid,)).fetchone()
    barracks=econ["buildings"]["barracks"]["level"]
    hq=econ["buildings"]["hq"]["level"]
    capacity=barracks*20
    units={}
    for key,u in UNITS.items():
        units[key]={"name":u["name"],"role":u["role"],"quantity":roster.get(key,0),
          "cost_per_unit":u["cost"],"seconds_per_unit":u["seconds"],"requires_hq":u["hq"],
          "unlocked":barracks>=1 and hq>=u["hq"]}
    return {"units":units,"queue":dict(queue) if queue else None,"capacity_per_batch":capacity,
      "barracks_level":barracks,"hq_level":hq,"resources":econ["resources"],"server_time":now,
      "total_troops":sum(roster.values())}

def register_military(app,database,get_user,valid_csrf):
    with database() as db:initialize(db)
    def own(db,uid,state):
        row=db.execute("SELECT id FROM ashfall_havens WHERE user_id=? AND state_id=?",(uid,state)).fetchone()
        if not row:raise HTTPException(404,"Haven not found")
        return row["id"]

    @app.get("/ashfall/api/military")
    async def military_status(request:Request,state_id:int=1):
        user=get_user(request.session.get("user_id"))
        if not user:raise HTTPException(401,"Sign in required")
        with database() as db:return snapshot(db,own(db,user["id"],state_id),time.time())

    @app.post("/ashfall/api/military/train")
    async def train(request:Request):
        user=get_user(request.session.get("user_id"))
        if not user:raise HTTPException(401,"Sign in required")
        form=await request.form()
        if not valid_csrf(request,str(form.get("csrf_token",""))):raise HTTPException(400,"Security token invalid")
        key=str(form.get("unit",""))
        if key not in UNITS:raise HTTPException(400,"Unknown troop class")
        try:state=int(form.get("state_id","1"));quantity=int(form.get("quantity","0"))
        except (ValueError,TypeError):raise HTTPException(400,"Invalid training request")
        if quantity<1 or quantity>1000:raise HTTPException(400,"Quantity must be 1–1000")
        now=time.time()
        with database() as db:
            hid=own(db,user["id"],state)
            current=snapshot(db,hid,now)
            if current["queue"]:raise HTTPException(409,"Training queue occupied")
            if not current["units"][key]["unlocked"]:raise HTTPException(409,"Barracks or Command Center level too low")
            if quantity>current["capacity_per_batch"]:raise HTTPException(409,"Exceeds Barracks batch capacity")
            cost={r:amount*quantity for r,amount in UNITS[key]["cost"].items()}
            if any(current["resources"][r]<v for r,v in cost.items()):raise HTTPException(409,"Insufficient resources")
            db.execute("UPDATE ashfall_resource_balances SET food=food-?,wood=wood-?,metal=metal-?,gas=gas-? WHERE haven_id=?",
                       (*(cost.get(r,0) for r in RES),hid))
            db.execute("INSERT INTO ashfall_training_queue(haven_id,unit_key,quantity,finishes_at) VALUES(?,?,?,?)",
                       (hid,key,quantity,now+quantity*UNITS[key]["seconds"]))
            return snapshot(db,hid,now)
