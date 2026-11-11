"""ASHFALL 0.8: peaceful wilderness gathering expeditions, server-side travel and return."""
import hashlib
import time
from fastapi import HTTPException, Request
from app.ashfall_military import snapshot as military_snapshot

RESOURCES=("food","wood","metal","gas")
def initialize(db):
    db.execute("""CREATE TABLE IF NOT EXISTS ashfall_expeditions(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
      node_key TEXT NOT NULL, resource TEXT NOT NULL,
      unit_key TEXT NOT NULL, quantity INTEGER NOT NULL,
      departed_at REAL NOT NULL, returns_at REAL NOT NULL,
      yield_amount INTEGER NOT NULL, claimed INTEGER NOT NULL DEFAULT 0 CHECK(claimed IN (0,1)))""")
    db.execute("CREATE INDEX IF NOT EXISTS idx_ashfall_expeditions_haven ON ashfall_expeditions(haven_id,claimed)")

def nodes(hid):
    result=[]
    for index,(resource,label) in enumerate((("food","Abandoned Greenhouse"),("wood","Fallen Timber"),("metal","Scrap Depot"),("gas","Fuel Cache"))):
        digest=hashlib.sha256(f"ashfall:expedition:{hid}:{index}".encode()).digest()
        result.append({"key":f"site_{index}","name":label,"resource":resource,
          "x":int.from_bytes(digest[:2],"big")%35-17,"y":int.from_bytes(digest[2:4],"big")%35-17,
          "travel_seconds":60+index*20,"yield_per_troop":10 if resource!="gas" else 4})
    return result

def settle(db,hid,now):
    # Complete and credit each return exactly once inside the caller's transaction.
    rows=db.execute("SELECT id,resource,yield_amount,unit_key,quantity FROM ashfall_expeditions WHERE haven_id=? AND claimed=0 AND returns_at<=?",(hid,now)).fetchall()
    for row in rows:
        updated=db.execute("UPDATE ashfall_expeditions SET claimed=1 WHERE id=? AND claimed=0",(row["id"],))
        if updated.rowcount:
            db.execute(f"UPDATE ashfall_resource_balances SET {row['resource']}={row['resource']}+? WHERE haven_id=?",(row["yield_amount"],hid))
            db.execute("INSERT OR IGNORE INTO ashfall_troops(haven_id,unit_key,quantity) VALUES(?,?,0)",(hid,row["unit_key"]))
            db.execute("UPDATE ashfall_troops SET quantity=quantity+? WHERE haven_id=? AND unit_key=?",(row["quantity"],hid,row["unit_key"]))

def snapshot(db,hid,now):
    military=military_snapshot(db,hid,now)
    settle(db,hid,now)
    roster={r["unit_key"]:r["quantity"] for r in db.execute("SELECT unit_key,quantity FROM ashfall_troops WHERE haven_id=?",(hid,))}
    active=db.execute("""SELECT id,node_key,resource,unit_key,quantity,departed_at,returns_at,yield_amount
      FROM ashfall_expeditions WHERE haven_id=? AND claimed=0 ORDER BY id""",(hid,)).fetchall()
    return {"nodes":nodes(hid),"active":[dict(r) for r in active],
      "troops_available":roster,"resources":dict(db.execute("SELECT food,wood,metal,gas FROM ashfall_resource_balances WHERE haven_id=?",(hid,)).fetchone()),
      "server_time":now,"march_slots":1}

def register_expeditions(app,database,get_user,valid_csrf):
    with database() as db:initialize(db)
    def own(db,uid,state):
        row=db.execute("SELECT id FROM ashfall_havens WHERE user_id=? AND state_id=?",(uid,state)).fetchone()
        if not row:raise HTTPException(404,"Haven not found")
        return row["id"]

    @app.get("/ashfall/api/expeditions")
    async def expedition_status(request:Request,state_id:int=1):
        user=get_user(request.session.get("user_id"))
        if not user:raise HTTPException(401,"Sign in required")
        with database() as db:return snapshot(db,own(db,user["id"],state_id),time.time())

    @app.post("/ashfall/api/expeditions/dispatch")
    async def dispatch(request:Request):
        user=get_user(request.session.get("user_id"))
        if not user:raise HTTPException(401,"Sign in required")
        form=await request.form()
        if not valid_csrf(request,str(form.get("csrf_token",""))):raise HTTPException(400,"Security token invalid")
        key=str(form.get("node",""))
        unit=str(form.get("unit",""))
        try:state=int(form.get("state_id","1"));quantity=int(form.get("quantity","0"))
        except (TypeError,ValueError):raise HTTPException(400,"Invalid expedition request")
        if unit not in ("infantry","rider","hunter") or not 1<=quantity<=1000:raise HTTPException(400,"Invalid troops")
        now=time.time()
        with database() as db:
            hid=own(db,user["id"],state)
            current=snapshot(db,hid,now)
            node=next((n for n in current["nodes"] if n["key"]==key),None)
            if not node:raise HTTPException(400,"Unknown gathering site")
            if current["active"]:raise HTTPException(409,"March slot occupied")
            if current["troops_available"].get(unit,0)<quantity:raise HTTPException(409,"Not enough available troops")
            db.execute("UPDATE ashfall_troops SET quantity=quantity-? WHERE haven_id=? AND unit_key=?",(quantity,hid,unit))
            duration=node["travel_seconds"]+quantity*2
            amount=quantity*node["yield_per_troop"]
            db.execute("""INSERT INTO ashfall_expeditions(haven_id,node_key,resource,unit_key,quantity,departed_at,returns_at,yield_amount)
              VALUES(?,?,?,?,?,?,?,?)""",(hid,key,node["resource"],unit,quantity,now,now+duration,amount))
            return snapshot(db,hid,now)
