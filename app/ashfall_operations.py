"""ASHFALL 2.2: one authoritative, state-scoped operations snapshot."""
import time
from fastapi import HTTPException, Request
from app.ashfall_expeditions import snapshot as expedition_snapshot
from app.ashfall_research import snapshot as research_snapshot
from app.ashfall_economy import snapshot as economy_snapshot

def construction_plan(buildings, balances, rates, queue, now):
    """Read-only next-upgrade estimates at current rates; never schedules purchases."""
    plans = []
    hq = buildings["hq"]["level"]
    for key, building in buildings.items():
        if building["level"] >= 30:
            status = "max_level"
        elif not building["unlocked"]:
            status = "locked"
        elif key != "hq" and building["next_level"] > hq:
            status = "requires_hq"
        elif key == "hq" and hq >= 2 and any(
            buildings[k]["level"] < hq - 1
            for k in ("farm", "lumber", "salvage", "fuel")
        ):
            status = "requires_production"
        else:
            status = "eligible"
        missing = {
            resource: max(0, int(amount) - int(balances.get(resource, 0)))
            for resource, amount in building["cost"].items()
            if amount > balances.get(resource, 0)
        }
        if status != "eligible":
            hours = None
        elif not missing:
            hours = 0.0
        elif any(rates.get(resource, 0) <= 0 for resource in missing):
            hours = None
            status = "needs_external_resources"
        else:
            hours = max(amount / rates[resource] for resource, amount in missing.items())
        wait_seconds = None if hours is None else int(__import__("math").ceil(hours * 3600))
        if status == "eligible" and queue:
            wait_seconds = max(wait_seconds, int(__import__("math").ceil(
                max(0, queue["finishes_at"] - now))))
            status = "queued_slot"
        plans.append({
            "key": key, "name": building["name"], "level": building["level"],
            "target_level": building["next_level"], "cost": building["cost"],
            "missing": missing, "status": status,
            "estimated_wait_seconds": wait_seconds,
            "build_seconds": building["seconds"],
        })
    return plans

def investment_analysis(plans, buildings, rates, multipliers):
    """Compare marginal production; mixed-resource costs are not payback."""
    resources = {"farm": "food", "lumber": "wood",
                 "salvage": "metal", "fuel": "gas"}
    bases = {"food": 120, "wood": 100, "metal": 80, "gas": 25}
    output = []
    for plan in plans:
        resource = resources.get(plan["key"])
        if not resource:
            continue
        level = buildings[plan["key"]]["level"]
        delta = rates[resource] * 0.18 if level else bases[resource] * multipliers[resource]
        total = sum(plan["cost"].values())
        output.append({
            "key": plan["key"], "name": plan["name"], "resource": resource,
            "additional_per_hour": round(delta, 2),
            "cost_total_units": total,
            "output_per_100_cost_units": round(delta * 100 / total, 2) if total else None,
            "status": plan["status"],
            "estimated_wait_seconds": plan["estimated_wait_seconds"]
        })
    output.sort(key=lambda item: (
        item["status"] not in ("eligible", "queued_slot"),
        -(item["output_per_100_cost_units"] or 0),
        item["name"]
    ))
    return output

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
    # Forecast current output only. Queued upgrades, future alliance changes,
    # and expedition returns are deliberately excluded from the projection.
    from app.ashfall_economy import BUILDINGS, RES
    from app.ashfall_alliance_technology import production_bonus
    research_levels = {row["tech_key"]: row["level"] for row in db.execute(
        "SELECT tech_key,level FROM ashfall_technology WHERE haven_id=?", (haven_id,))}
    resource_tech = {"food": "agriculture", "wood": "forestry",
                     "metal": "metallurgy", "gas": "fuel_processing"}
    rates = {resource: 0.0 for resource in RES}
    for key, building in economy["buildings"].items():
        definition = BUILDINGS[key]
        resource = definition["resource"]
        if resource and building["level"] > 0:
            rates[resource] += (
                definition["rate"] * 1.18 ** (building["level"] - 1)
                * (1 + 0.1 * research_levels.get(resource_tech[resource], 0))
                * (1 + production_bonus(db, haven_id, resource))
            )
    forecast = {
        resource: {
            "per_hour": round(rates[resource], 2),
            "in_1h": resources[resource] + int(rates[resource]),
            "in_6h": resources[resource] + int(rates[resource] * 6),
            "in_24h": resources[resource] + int(rates[resource] * 24),
        } for resource in RES
    }
    plans = construction_plan(economy["buildings"], resources, rates, dict(construction) if construction else None, now)
    multipliers = {
        resource: (1 + 0.1 * research_levels.get(resource_tech[resource], 0))
        * (1 + production_bonus(db, haven_id, resource))
        for resource in RES
    }
    investments = investment_analysis(plans, economy["buildings"], rates, multipliers)
    return {
        "investment_analysis": investments,
        "construction_plans": plans,
        "forecast": forecast,
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
