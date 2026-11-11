"""ASHFALL 2.2: one authoritative, state-scoped operations snapshot."""
import time
from fastapi import HTTPException, Request
from app.ashfall_expeditions import snapshot as expedition_snapshot
from app.ashfall_research import snapshot as research_snapshot
from app.ashfall_economy import snapshot as economy_snapshot

def snapshot(db, haven_id, now):
    # Expeditions settle military training and economy before we read queues.
    expedition = expedition_snapshot(db, haven_id, now)
    research = research_snapshot(db, haven_id, now)
    economy = economy_snapshot(db, haven_id, now)
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
    recommendations = []
    resources = expedition["resources"]

    def shortage(cost):
        return {key: amount - resources.get(key, 0)
                for key, amount in cost.items() if amount > resources.get(key, 0)}

    if construction:
        recommendations.append({"priority": "active", "title": "Construction underway",
                                "detail": "Your builders are occupied.", "action": "settlement"})
    else:
        candidates = []
        for key, building in economy["buildings"].items():
            if not building["unlocked"] or building["level"] >= 30:
                continue
            if key != "hq" and building["next_level"] > economy["buildings"]["hq"]["level"]:
                continue
            if key == "hq" and building["level"] >= 2 and any(
                economy["buildings"][k]["level"] < building["level"] - 1
                for k in ("farm", "lumber", "salvage", "fuel")
            ):
                continue
            candidates.append((building, shortage(building["cost"])))
        ready = [item for item in candidates if not item[1]]
        if ready:
            building, _ = min(ready, key=lambda item: (item[0]["level"], sum(item[0]["cost"].values())))
            recommendations.append({"priority": "ready",
                                    "title": building["name"] + " can be upgraded",
                                    "detail": "All required resources are available.",
                                    "action": "settlement"})
        elif candidates:
            building, missing = min(candidates, key=lambda item: sum(item[1].values()))
            recommendations.append({"priority": "shortage",
                                    "title": "Next construction opportunity",
                                    "detail": building["name"] + " needs " + ", ".join(
                                        str(amount) + " " + key for key, amount in missing.items()),
                                    "action": "settlement"})

    if research["queue"]:
        recommendations.append({"priority": "active", "title": "Research underway",
                                "detail": "A technology project is in progress.",
                                "action": "researchButton"})
    else:
        candidates = [(tech, shortage(tech["cost"]))
                      for tech in research["technologies"].values()
                      if tech["unlocked"] and tech["level"] < tech["max_level"]]
        ready = [item for item in candidates if not item[1]]
        if ready:
            tech, _ = min(ready, key=lambda item: (item[0]["level"], sum(item[0]["cost"].values())))
            recommendations.append({"priority": "ready",
                                    "title": tech["name"] + " is available",
                                    "detail": "Resources cover the next research level.",
                                    "action": "researchButton"})
        elif candidates:
            tech, missing = min(candidates, key=lambda item: sum(item[1].values()))
            recommendations.append({"priority": "shortage",
                                    "title": "Next research opportunity",
                                    "detail": tech["name"] + " needs " + ", ".join(
                                        str(amount) + " " + key for key, amount in missing.items()),
                                    "action": "researchButton"})

    if not expedition["active"]:
        recommendations.append({"priority": "opportunity",
                                "title": "Wilderness march slot available",
                                "detail": "Gathering is available if troops are ready.",
                                "action": "expeditionButton"})
    return {
        "recommendations": recommendations,
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
