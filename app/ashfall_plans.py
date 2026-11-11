"""ASHFALL 3.9 — player-owned persistent expedition destination.

A plan is a bookmark, not an automatic mission. Routes and progress are
recomputed against the player's own discoveries on every read.
"""
import time
from fastapi import HTTPException, Request
from app.ashfall_world import SECTOR_SIZE
from app.ashfall_routes import plan_route


def plan_snapshot(home, target, discovered, updated_at):
    route = plan_route(home, target, discovered)
    total = len(route["path"])
    charted = route["known_steps"]
    return {
        "target": {"x": target[0], "y": target[1]},
        "updated_at": updated_at,
        "charted_steps": charted,
        "total_steps": total,
        "progress_percent": round(100 * charted / total) if total else 100,
        "complete": route["unknown_steps"] == 0,
        "route": route,
    }


def register_expedition_plans(app, database, get_user, valid_csrf):
    with database() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS ashfall_expedition_plans (
            haven_id INTEGER PRIMARY KEY REFERENCES ashfall_havens(id) ON DELETE CASCADE,
            state_id INTEGER NOT NULL,
            target_x INTEGER NOT NULL CHECK(target_x BETWEEN 0 AND 15),
            target_y INTEGER NOT NULL CHECK(target_y BETWEEN 0 AND 15),
            updated_at REAL NOT NULL
        )""")

    def require_user(request):
        user = get_user(request.session.get("user_id"))
        if not user:
            raise HTTPException(401, "Sign in required")
        return user

    def haven_for(db, user_id, state_id):
        haven = db.execute("""SELECT h.id,p.x,p.y FROM ashfall_havens h
            JOIN ashfall_world_positions p ON p.haven_id=h.id
            WHERE h.user_id=? AND h.state_id=?""", (user_id, state_id)).fetchone()
        if not haven:
            raise HTTPException(404, "Haven not found in this state")
        return haven

    def snapshot(db, haven, state_id):
        row = db.execute("""SELECT target_x,target_y,updated_at
            FROM ashfall_expedition_plans WHERE haven_id=? AND state_id=?""",
            (haven["id"], state_id)).fetchone()
        if row is None:
            return None
        discovered = {(r["sector_x"], r["sector_y"]) for r in db.execute(
            """SELECT sector_x,sector_y FROM ashfall_sector_discoveries
            WHERE haven_id=? AND state_id=?""", (haven["id"], state_id))}
        home = (haven["x"] // SECTOR_SIZE, haven["y"] // SECTOR_SIZE)
        return plan_snapshot(home, (row["target_x"], row["target_y"]),
                             discovered, row["updated_at"])

    @app.get("/ashfall/api/atlas/plan")
    async def get_expedition_plan(request: Request, state_id: int = 1):
        user = require_user(request)
        with database() as db:
            haven = haven_for(db, user["id"], state_id)
            result = snapshot(db, haven, state_id)
        return {"state_id": state_id, "plan": result}

    @app.post("/ashfall/api/atlas/plan")
    async def save_expedition_plan(request: Request):
        user = require_user(request)
        form = await request.form()
        if not valid_csrf(request, str(form.get("csrf_token", ""))):
            raise HTTPException(400, "Invalid security token")
        try:
            state_id = int(form.get("state_id", "1"))
            x = int(form.get("target_x", "-1"))
            y = int(form.get("target_y", "-1"))
        except (TypeError, ValueError):
            raise HTTPException(400, "Invalid expedition coordinates")
        if not (0 <= x < 16 and 0 <= y < 16):
            raise HTTPException(400, "Target outside world bounds")
        with database() as db:
            db.execute("BEGIN IMMEDIATE")
            haven = haven_for(db, user["id"], state_id)
            db.execute("""INSERT INTO ashfall_expedition_plans
                (haven_id,state_id,target_x,target_y,updated_at)
                VALUES(?,?,?,?,?)
                ON CONFLICT(haven_id) DO UPDATE SET
                state_id=excluded.state_id,
                target_x=excluded.target_x,
                target_y=excluded.target_y,
                updated_at=excluded.updated_at""",
                (haven["id"], state_id, x, y, time.time()))
            result = snapshot(db, haven, state_id)
        return {"state_id": state_id, "plan": result, "saved": True}

    @app.post("/ashfall/api/atlas/plan/clear")
    async def clear_expedition_plan(request: Request):
        user = require_user(request)
        form = await request.form()
        if not valid_csrf(request, str(form.get("csrf_token", ""))):
            raise HTTPException(400, "Invalid security token")
        try:
            state_id = int(form.get("state_id", "1"))
        except (TypeError, ValueError):
            raise HTTPException(400, "Invalid state")
        with database() as db:
            db.execute("BEGIN IMMEDIATE")
            haven = haven_for(db, user["id"], state_id)
            db.execute("DELETE FROM ashfall_expedition_plans WHERE haven_id=? AND state_id=?",
                       (haven["id"], state_id))
        return {"state_id": state_id, "plan": None, "cleared": True}
