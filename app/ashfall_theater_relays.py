"""ASHFALL 4.5 — durable, resource-backed regional survey relays.

One relay per charted theater. Resource deduction and construction are atomic.
No passive production bonuses or territorial ownership are implied.
"""
import time
from fastapi import HTTPException, Request
from app.ashfall_economy import accrue

COST = {"wood": 180, "metal": 100, "gas": 25}
BUILD_SECONDS = 300
THEATER_SIZE = 4

def theater_id(x, y):
    if not (isinstance(x, int) and isinstance(y, int) and 0 <= x < 4 and 0 <= y < 4):
        raise ValueError("Invalid theater")
    return f"T-{x+1}{y+1}"

def relay_snapshot(db, haven_id, state_id, now=None):
    now = time.time() if now is None else now
    rows = db.execute("""SELECT theater_x,theater_y,started_at,finishes_at
        FROM ashfall_theater_relays WHERE haven_id=? AND state_id=?
        ORDER BY theater_y,theater_x""", (haven_id, state_id)).fetchall()
    installations = []
    for row in rows:
        remaining = max(0, int(row["finishes_at"] - now + 0.999))
        installations.append({"id": theater_id(row["theater_x"],row["theater_y"]),
            "theater_x": row["theater_x"],"theater_y":row["theater_y"],
            "started_at":row["started_at"],"finishes_at":row["finishes_at"],
            "remaining_seconds":remaining,
            "status":"BUILDING" if remaining else "OPERATIONAL"})
    network=relay_network_snapshot(db,haven_id,state_id,now)
    return {"installations":installations,"network":network,"cost":COST,"build_seconds":BUILD_SECONDS,
            "note":"Operational relays grant 10% scouting speed, or 15% when linked to an adjacent operational relay. No resource generation or territorial claims."}

def scouting_relay_bonus(db, haven_id, state_id, sector_x, sector_y, now):
    """10% local speed; 15% with an orthogonally adjacent online relay."""
    if not (0 <= sector_x < 16 and 0 <= sector_y < 16):
        raise ValueError("Sector outside world bounds")
    tx, ty = sector_x // 4, sector_y // 4
    online = {(r[0], r[1]) for r in db.execute(
        """SELECT theater_x,theater_y FROM ashfall_theater_relays
        WHERE haven_id=? AND state_id=? AND finishes_at<=?""",
        (haven_id, state_id, now))}
    if (tx,ty) not in online:
        return 0
    linked = any((tx+dx,ty+dy) in online for dx,dy in
                 ((1,0),(-1,0),(0,1),(0,-1)))
    from app.ashfall_relay_upgrades import effective_level
    has_upgrades=db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='ashfall_relay_upgrades'"
    ).fetchone()
    upgrade=db.execute("""SELECT level,finishes_at FROM ashfall_relay_upgrades
        WHERE haven_id=? AND state_id=? AND theater_x=? AND theater_y=?""",
        (haven_id,state_id,tx,ty)).fetchone() if has_upgrades else None
    level=effective_level(upgrade,now) if upgrade else 1
    from app.ashfall_relay_doctrines import doctrine_bonus, doctrine_for
    has_doctrines=db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='ashfall_relay_doctrines'"
    ).fetchone()
    doctrine=doctrine_for(db,haven_id,state_id,tx,ty) if has_doctrines else None
    # Doctrine and upgrade bonuses apply only to newly launched scouting missions.
    return (15 if linked else 10)+3*(level-1)+doctrine_bonus(doctrine,linked)


def relay_network_snapshot(db, haven_id, state_id, now):
    online = {(r[0],r[1]) for r in db.execute(
        """SELECT theater_x,theater_y FROM ashfall_theater_relays
        WHERE haven_id=? AND state_id=? AND finishes_at<=?""",
        (haven_id,state_id,now))}
    linked = sorted((x,y) for x,y in online if any(
        (x+dx,y+dy) in online for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))))
    from app.ashfall_relay_corridors import relay_corridors
    charted={(r["sector_x"]//4,r["sector_y"]//4) for r in db.execute(
        "SELECT sector_x,sector_y FROM ashfall_sector_discoveries WHERE haven_id=? AND state_id=?",
        (haven_id,state_id))}
    home=db.execute("SELECT x,y FROM ashfall_world_positions WHERE haven_id=? AND state_id=?",
                    (haven_id,state_id)).fetchone()
    if home:
        charted.add((home["x"]//512,home["y"]//512))
    corridors=relay_corridors(online,charted)
    return {"corridors":corridors,"operational_relays":len(online),
            "linked_relays":len(linked),
            "linked_theaters":[theater_id(x,y) for x,y in linked],
            "base_scout_speed_bonus_percent":10,
            "linked_scout_speed_bonus_percent":15,
            "note":"Adjacent operational relays share intelligence. Bonuses apply only to new scouting missions in their own theater."}


def relay_build_readiness(db, haven_id, state_id, now):
    """Read-only, server-authoritative construction eligibility by theater."""
    from app.ashfall_economy import snapshot
    economy = snapshot(db, haven_id, now)
    balances = economy["resources"]
    position = db.execute(
        "SELECT x,y FROM ashfall_world_positions WHERE haven_id=? AND state_id=?",
        (haven_id,state_id)).fetchone()
    if position is None:
        return []
    home=(position["x"]//128,position["y"]//128)
    charted={(r["sector_x"]//4,r["sector_y"]//4) for r in db.execute(
        "SELECT sector_x,sector_y FROM ashfall_sector_discoveries WHERE haven_id=? AND state_id=?",
        (haven_id,state_id))}
    built={(r["theater_x"],r["theater_y"]) for r in db.execute(
        "SELECT theater_x,theater_y FROM ashfall_theater_relays WHERE haven_id=? AND state_id=?",
        (haven_id,state_id))}
    result=[]
    for y in range(4):
        for x in range(4):
            missing={key:max(0,amount-balances.get(key,0)) for key,amount in COST.items()}
            if (x,y) in built:
                reason="ALREADY BUILT"
            elif (x,y) not in charted and (x,y)!=(home[0]//4,home[1]//4):
                reason="THEATER UNCHARTED"
            elif any(missing.values()):
                reason="INSUFFICIENT RESOURCES"
            else:
                reason="READY"
            result.append({"theater_x":x,"theater_y":y,"id":theater_id(x,y),
                           "can_build":reason=="READY","reason":reason,
                           "missing_resources":missing})
    return result


def register_theater_relays(app, database, get_user, valid_csrf):
    with database() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS ashfall_theater_relays(
            haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
            state_id INTEGER NOT NULL,
            theater_x INTEGER NOT NULL CHECK(theater_x BETWEEN 0 AND 3),
            theater_y INTEGER NOT NULL CHECK(theater_y BETWEEN 0 AND 3),
            started_at REAL NOT NULL,
            finishes_at REAL NOT NULL,
            PRIMARY KEY(haven_id,state_id,theater_x,theater_y))""")

    def haven(db,request,state_id):
        user=get_user(request.session.get("user_id"))
        if not user: raise HTTPException(401,"Sign in required")
        row=db.execute("SELECT id FROM ashfall_havens WHERE user_id=? AND state_id=?",
                       (user["id"],state_id)).fetchone()
        if not row: raise HTTPException(404,"Haven not found")
        return row["id"]

    @app.get("/ashfall/api/atlas/relays")
    async def get_relays(request:Request,state_id:int=1):
        with database() as db:
            hid=haven(db,request,state_id)
            now=time.time()
            db.execute("BEGIN IMMEDIATE")
            result=relay_snapshot(db,hid,state_id,now)
            result["readiness"]=relay_build_readiness(db,hid,state_id,now)
            result["server_time"]=now
            return result

    @app.post("/ashfall/api/atlas/relays/build")
    async def build_relay(request:Request):
        form=await request.form()
        if not valid_csrf(request,str(form.get("csrf_token",""))):
            raise HTTPException(400,"Invalid security token")
        try:
            state_id=int(form.get("state_id","1"))
            tx=int(form.get("theater_x","-1"))
            ty=int(form.get("theater_y","-1"))
            theater_id(tx,ty)
        except (TypeError,ValueError):
            raise HTTPException(400,"Invalid theater coordinates")
        now=time.time()
        with database() as db:
            db.execute("BEGIN IMMEDIATE")
            hid=haven(db,request,state_id)
            if db.execute("""SELECT 1 FROM ashfall_theater_relays
                WHERE haven_id=? AND state_id=? AND theater_x=? AND theater_y=?""",
                (hid,state_id,tx,ty)).fetchone():
                raise HTTPException(409,"A relay already exists in this theater")
            # The Haven's own charted cells are the only eligible sites.
            origin=db.execute("""SELECT p.x,p.y FROM ashfall_world_positions p
                WHERE p.haven_id=? AND p.state_id=?""",(hid,state_id)).fetchone()
            home=(origin["x"]//128,origin["y"]//128)
            charted=db.execute("""SELECT 1 FROM ashfall_sector_discoveries
                WHERE haven_id=? AND state_id=?
                AND sector_x BETWEEN ? AND ? AND sector_y BETWEEN ? AND ? LIMIT 1""",
                (hid,state_id,tx*4,tx*4+3,ty*4,ty*4+3)).fetchone()
            if not charted and not (tx*4<=home[0]<tx*4+4 and ty*4<=home[1]<ty*4+4):
                raise HTTPException(403,"Chart a sector in this theater before building")
            accrue(db,hid,now)
            balance=db.execute("SELECT wood,metal,gas FROM ashfall_resource_balances WHERE haven_id=?",
                               (hid,)).fetchone()
            if not balance or any(balance[key]<amount for key,amount in COST.items()):
                raise HTTPException(409,"Insufficient resources for a survey relay")
            db.execute("""UPDATE ashfall_resource_balances
                SET wood=wood-?,metal=metal-?,gas=gas-? WHERE haven_id=?""",
                (COST["wood"],COST["metal"],COST["gas"],hid))
            db.execute("""INSERT INTO ashfall_theater_relays
                (haven_id,state_id,theater_x,theater_y,started_at,finishes_at)
                VALUES(?,?,?,?,?,?)""",(hid,state_id,tx,ty,now,now+BUILD_SECONDS))
            return relay_snapshot(db,hid,state_id,now)
