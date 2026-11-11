"""ASHFALL 5.0 — durable industrial relay upgrades.

Upgrades are atomic, consume real Haven resources and finish on server time.
They improve regional scouting, not resource production or territorial control.
"""
import time
from fastapi import HTTPException, Request
from app.ashfall_economy import accrue

MAX_LEVEL=3
UPGRADE_COSTS={
    2:{"wood":300,"metal":180,"gas":60},
    3:{"wood":600,"metal":360,"gas":120},
}
UPGRADE_SECONDS={2:600,3:1200}

def effective_level(row,now):
    if row is None:return 0
    level=row["level"]
    return level+1 if row["finishes_at"] is not None and row["finishes_at"]<=now else level

def upgrade_status(db,haven_id,state_id,now):
    rows=db.execute("""SELECT theater_x,theater_y,level,finishes_at
        FROM ashfall_relay_upgrades WHERE haven_id=? AND state_id=?""",
        (haven_id,state_id)).fetchall()
    records={(r["theater_x"],r["theater_y"]):r for r in rows}
    installed=db.execute("""SELECT theater_x,theater_y,finishes_at FROM ashfall_theater_relays
        WHERE haven_id=? AND state_id=?""",(haven_id,state_id)).fetchall()
    result=[]
    for relay in installed:
        x,y=relay["theater_x"],relay["theater_y"]
        record=records.get((x,y))
        level=effective_level(record,now) if record else 1
        upgrading=bool(record and record["finishes_at"] is not None and record["finishes_at"]>now)
        if relay["finishes_at"]>now:upgrading=False
        next_level=level+1 if level<MAX_LEVEL else None
        result.append({"theater_x":x,"theater_y":y,"id":f"T-{x+1}{y+1}",
            "level":level,"max_level":MAX_LEVEL,
            "relay_operational":relay["finishes_at"]<=now,
            "upgrading":upgrading,
            "upgrade_remaining_seconds":max(0,int(record["finishes_at"]-now+0.999)) if upgrading else 0,
            "next_level":next_level,
            "next_cost":UPGRADE_COSTS.get(next_level),
            "next_seconds":UPGRADE_SECONDS.get(next_level)})
    return result

def register_relay_upgrades(app,database,get_user,valid_csrf):
    with database() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS ashfall_relay_upgrades(
            haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
            state_id INTEGER NOT NULL,
            theater_x INTEGER NOT NULL CHECK(theater_x BETWEEN 0 AND 3),
            theater_y INTEGER NOT NULL CHECK(theater_y BETWEEN 0 AND 3),
            level INTEGER NOT NULL DEFAULT 1 CHECK(level BETWEEN 1 AND 3),
            finishes_at REAL,
            PRIMARY KEY(haven_id,state_id,theater_x,theater_y))""")

    @app.get("/ashfall/api/atlas/relay-upgrades")
    async def get_upgrades(request:Request,state_id:int=1):
        user=get_user(request.session.get("user_id"))
        if not user:raise HTTPException(401,"Sign in required")
        with database() as db:
            haven=db.execute("SELECT id FROM ashfall_havens WHERE user_id=? AND state_id=?",
                             (user["id"],state_id)).fetchone()
            if not haven:raise HTTPException(404,"Haven not found")
            return {"upgrades":upgrade_status(db,haven["id"],state_id,time.time())}

    @app.post("/ashfall/api/atlas/relay-upgrades/start")
    async def start_upgrade(request:Request):
        user=get_user(request.session.get("user_id"))
        if not user:raise HTTPException(401,"Sign in required")
        form=await request.form()
        if not valid_csrf(request,str(form.get("csrf_token",""))):
            raise HTTPException(400,"Invalid security token")
        try:
            state_id=int(form.get("state_id","1"))
            x=int(form.get("theater_x","-1"))
            y=int(form.get("theater_y","-1"))
        except (TypeError,ValueError):
            raise HTTPException(400,"Invalid coordinates")
        if not (0<=x<4 and 0<=y<4):raise HTTPException(400,"Invalid theater")
        now=time.time()
        with database() as db:
            db.execute("BEGIN IMMEDIATE")
            haven=db.execute("SELECT id FROM ashfall_havens WHERE user_id=? AND state_id=?",
                             (user["id"],state_id)).fetchone()
            if not haven:raise HTTPException(404,"Haven not found")
            hid=haven["id"]
            relay=db.execute("""SELECT finishes_at FROM ashfall_theater_relays
                WHERE haven_id=? AND state_id=? AND theater_x=? AND theater_y=?""",
                (hid,state_id,x,y)).fetchone()
            if not relay or relay["finishes_at"]>now:
                raise HTTPException(409,"An operational relay is required")
            record=db.execute("""SELECT level,finishes_at FROM ashfall_relay_upgrades
                WHERE haven_id=? AND state_id=? AND theater_x=? AND theater_y=?""",
                (hid,state_id,x,y)).fetchone()
            if record and record["finishes_at"] is not None and record["finishes_at"]>now:
                raise HTTPException(409,"This relay is already upgrading")
            level=effective_level(record,now) if record else 1
            if level>=MAX_LEVEL:raise HTTPException(409,"Relay is at maximum level")
            target=level+1
            cost=UPGRADE_COSTS[target]
            accrue(db,hid,now)
            balance=db.execute("SELECT wood,metal,gas FROM ashfall_resource_balances WHERE haven_id=?",
                               (hid,)).fetchone()
            if any(balance[k]<v for k,v in cost.items()):
                raise HTTPException(409,"Insufficient resources for relay upgrade")
            db.execute("""UPDATE ashfall_resource_balances
                SET wood=wood-?,metal=metal-?,gas=gas-? WHERE haven_id=?""",
                (cost["wood"],cost["metal"],cost["gas"],hid))
            db.execute("""INSERT INTO ashfall_relay_upgrades
                (haven_id,state_id,theater_x,theater_y,level,finishes_at)
                VALUES(?,?,?,?,?,?)
                ON CONFLICT(haven_id,state_id,theater_x,theater_y)
                DO UPDATE SET level=excluded.level,finishes_at=excluded.finishes_at""",
                (hid,state_id,x,y,level,now+UPGRADE_SECONDS[target]))
            return {"started":True,"target_level":target,
                    "finishes_at":now+UPGRADE_SECONDS[target],
                    "cost":cost}
