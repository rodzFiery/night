"""ASHFALL 3.2 — durable reconnaissance with server-authoritative completion."""
import time
from fastapi import HTTPException, Request
from app.ashfall_world import SECTOR_SIZE, sector_profile

def scout_duration(threat):
    return 90 + 30 * threat

def register_scouting(app, database, get_user, valid_csrf):
    def require_user(request):
        user = get_user(request.session.get("user_id"))
        if not user:
            raise HTTPException(401, "Sign in required")
        return user

    async def verified_form(request):
        form = await request.form()
        if not valid_csrf(request, str(form.get("csrf_token", ""))):
            raise HTTPException(400, "Invalid security token")
        return form

    @app.post("/ashfall/api/atlas/discover")
    async def start_scout(request: Request):
        user = require_user(request)
        form = await verified_form(request)
        try:
            state_id = int(form.get("state_id", "1"))
            x = int(form.get("sector_x", "-1"))
            y = int(form.get("sector_y", "-1"))
        except (TypeError, ValueError):
            raise HTTPException(400, "Invalid sector coordinates")
        if not (0 <= x < 16 and 0 <= y < 16):
            raise HTTPException(400, "Sector outside world bounds")
        with database() as db:
            db.execute("BEGIN IMMEDIATE")
            haven = db.execute("""SELECT h.id,p.x,p.y FROM ashfall_havens h
                JOIN ashfall_world_positions p ON p.haven_id=h.id
                WHERE h.user_id=? AND h.state_id=?""",
                (user["id"],state_id)).fetchone()
            if not haven:
                raise HTTPException(404, "Haven not found")
            hx, hy = haven["x"] // SECTOR_SIZE, haven["y"] // SECTOR_SIZE
            if max(abs(x-hx), abs(y-hy)) > 1:
                raise HTTPException(403, "Only adjacent sectors can be surveyed")
            if (x,y) == (hx,hy):
                raise HTTPException(409, "Home sector is already known")
            if db.execute("""SELECT 1 FROM ashfall_sector_discoveries
                WHERE haven_id=? AND sector_x=? AND sector_y=?""",
                (haven["id"],x,y)).fetchone():
                raise HTTPException(409, "Sector already surveyed")
            if db.execute("SELECT 1 FROM ashfall_scout_missions WHERE haven_id=?",
                          (haven["id"],)).fetchone():
                raise HTTPException(409, "A reconnaissance mission is already active")
            now = time.time()
            duration = scout_duration(sector_profile(state_id,x,y)["threat"])
            db.execute("""INSERT INTO ashfall_scout_missions
                (haven_id,state_id,sector_x,sector_y,started_at,finishes_at)
                VALUES(?,?,?,?,?,?)""",(haven["id"],state_id,x,y,now,now+duration))
        return {"started":True,"sector_x":x,"sector_y":y,
                "finishes_at":now+duration,"duration_seconds":duration}

    @app.post("/ashfall/api/atlas/claim")
    async def claim_scout(request: Request):
        user = require_user(request)
        form = await verified_form(request)
        try:
            state_id = int(form.get("state_id", "1"))
        except (TypeError, ValueError):
            raise HTTPException(400, "Invalid state")
        with database() as db:
            db.execute("BEGIN IMMEDIATE")
            haven = db.execute(
                "SELECT id FROM ashfall_havens WHERE user_id=? AND state_id=?",
                (user["id"],state_id)).fetchone()
            if not haven:
                raise HTTPException(404, "Haven not found")
            mission = db.execute(
                "SELECT * FROM ashfall_scout_missions WHERE haven_id=? AND state_id=?",
                (haven["id"],state_id)).fetchone()
            if not mission:
                raise HTTPException(409, "No reconnaissance mission to claim")
            if time.time() < mission["finishes_at"]:
                raise HTTPException(409, "Reconnaissance still underway")
            db.execute("""INSERT OR IGNORE INTO ashfall_sector_discoveries
                (haven_id,state_id,sector_x,sector_y,discovered_at)
                VALUES(?,?,?,?,?)""",
                (haven["id"],state_id,mission["sector_x"],mission["sector_y"],time.time()))
            db.execute("DELETE FROM ashfall_scout_missions WHERE haven_id=?",(haven["id"],))
        return {"claimed":True,"sector_x":mission["sector_x"],
                "sector_y":mission["sector_y"]}
