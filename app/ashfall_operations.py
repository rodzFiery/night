"""ASHFALL 2.2: one authoritative, state-scoped operations snapshot."""
import time
from fastapi import HTTPException, Request
from app.ashfall_expeditions import snapshot as expedition_snapshot
from app.ashfall_research import snapshot as research_snapshot

def snapshot(db, haven_id, now):
    # Expeditions settle military training and economy before we read queues.
    expedition = expedition_snapshot(db, haven_id, now)
    research = research_snapshot(db, haven_id, now)
    construction = db.execute(
        "SELECT building_key,target_level,finishes_at FROM ashfall_construction_queue WHERE haven_id=?",
        (haven_id,)
    ).fetchone()
    training = db.execute(
        "SELECT unit_key,quantity,finishes_at FROM ashfall_training_queue WHERE haven_id=?",
        (haven_id,)
    ).fetchone()
    roster = db.execute(
        "SELECT COALESCE(SUM(quantity),0) AS total FROM ashfall_troops WHERE haven_id=?",
        (haven_id,)
    ).fetchone()
    return {
        "server_time": now,
        "resources": expedition["resources"],
        "construction": dict(construction) if construction else None,
        "research": research["queue"],
        "training": dict(training) if training else None,
        "expeditions": expedition["active"],
        "total_troops": roster["total"],
        "hq_level": research["hq_level"],
        "research_names": {key: value["name"] for key, value in research["technologies"].items()},
    }

def register_operations(app, database, get_user):
    @app.get("/ashfall/api/operations")
    async def operations(request: Request, state_id: int = 1):
        user = get_user(request.session.get("user_id"))
        if not user:
            raise HTTPException(401, "Sign in required")
        with database() as db:
            # Settling timed work writes to the database; serialize this snapshot.
            db.execute("BEGIN IMMEDIATE")
            haven = db.execute(
                "SELECT id FROM ashfall_havens WHERE user_id=? AND state_id=?",
                (user["id"], state_id)
            ).fetchone()
            if not haven:
                raise HTTPException(404, "Haven not found")
            return snapshot(db, haven["id"], time.time())
