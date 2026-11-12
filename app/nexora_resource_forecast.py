"""NEXORA 77 — read-only construction quotes for the settlement roadmap.

Quotes reuse ASHFALL's actual construction pricing and prerequisites. They are
snapshots of persisted balances; they do not accrue offline production or
reserve resources. The upgrade endpoint remains authoritative.
"""
import math
from app.ashfall_economy import BUILDINGS, RES
from app import ashfall_crystal_age as crystal


def _quote(db, haven_id, levels, balances, rare, queue, architecture, key):
    definition = BUILDINGS[key]
    level = levels[key]
    if level >= crystal.MAX_LEVEL:
        return {"key": key, "level": level, "blocked": ["Maximum level reached"],
                "affordable": False, "cost": {}, "shortages": {}, "rare_cost": {},
                "rare_shortages": {}, "seconds": 0}
    costs = crystal.conventional_cost(definition["cost"], level, 1 if key == "hq" else 0)
    rare_cost = crystal.crystal_cost(level) if level >= crystal.NORMAL_CAP else {}
    if rare_cost:
        rare_cost = {name: max(1, int(math.ceil(amount * (1 - .03 * architecture))))
                     if amount else 0 for name, amount in rare_cost.items()}
    seconds = crystal.construction_seconds(definition["seconds"], level, 1 if key == "hq" else 0)
    blocked = []
    if queue:
        blocked.append("Construction slot occupied")
    if level >= 30 and levels["hq"] < 30:
        blocked.append("Crystal Age requires Command Center level 30")
    if key != "hq" and level + 1 > levels["hq"]:
        blocked.append("Upgrade Command Center first")
    if key == "hq" and level >= 2 and any(
        levels[name] < level - 1 for name in ("farm", "lumber", "salvage", "fuel")
    ):
        blocked.append("Develop production buildings first")
    shortages = {name: max(0, amount - balances.get(name, 0))
                 for name, amount in costs.items() if amount > balances.get(name, 0)}
    rare_shortages = {name: max(0, amount - rare.get(name, 0))
                      for name, amount in rare_cost.items() if amount > rare.get(name, 0)}
    return {
        "key": key, "level": level, "next_level": level + 1,
        "cost": costs, "rare_cost": rare_cost, "seconds": seconds,
        "shortages": shortages, "rare_shortages": rare_shortages,
        "blocked": blocked,
        "affordable": not blocked and not shortages and not rare_shortages,
    }


def resource_forecast(db, user_id, roadmap):
    """Quote roadmap steps for owned Havens; no mutations or client-supplied levels."""
    owned = {int(row["id"]) for row in db.execute(
        "SELECT id FROM ashfall_havens WHERE user_id=?", (user_id,)
    )}
    reports = []
    for haven in roadmap["havens"]:
        haven_id = int(haven["haven_id"])
        if haven_id not in owned:
            raise ValueError("Roadmap contains a Haven not owned by this player")
        if haven["complete"]:
            reports.append({"haven_id": haven_id, "quotes": [], "queue_occupied": False})
            continue
        levels = {row["building_key"]: int(row["level"]) for row in db.execute(
            "SELECT building_key,level FROM ashfall_building_levels WHERE haven_id=?", (haven_id,)
        )}
        # Missing rows are uninitialized, not credited building levels.
        # Match settlement intelligence so new Haven profiles never fail.
        levels = {key: levels.get(key, 0) for key in BUILDINGS}
        balance_row = db.execute(
            "SELECT food,wood,metal,gas FROM ashfall_resource_balances WHERE haven_id=?", (haven_id,)
        ).fetchone()
        balances = {key: int(balance_row[key]) if balance_row else 0 for key in RES}
        rare_row = db.execute(
            "SELECT crystal_shards,ancient_cores,prismatic_essence FROM ashfall_crystal_balances WHERE haven_id=?",
            (haven_id,),
        ).fetchone()
        rare = {key: int(rare_row[key]) if rare_row else 0 for key in crystal.RARE_MATERIALS}
        queue = db.execute(
            "SELECT building_key FROM ashfall_construction_queue WHERE haven_id=?", (haven_id,)
        ).fetchone()
        # Frontier research is an optional late-game module. Fresh installations
        # may not have its table yet; an absent table means no architecture bonus.
        has_research = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='ashfall_crystal_frontier_research'"
        ).fetchone()
        architecture_row = (db.execute(
            "SELECT level FROM ashfall_crystal_frontier_research WHERE haven_id=? AND tech_key='prismatic_architecture'",
            (haven_id,),
        ).fetchone() if has_research else None)
        architecture = int(architecture_row["level"]) if architecture_row else 0
        quotes = []
        for step in haven["steps"]:
            key = step["key"]
            if key not in BUILDINGS or step["current"] != levels[key]:
                raise ValueError("Roadmap step is stale or invalid")
            quotes.append({**_quote(db, haven_id, levels, balances, rare, queue,
                                    architecture, key), "priority": step["priority"],
                           "name": BUILDINGS[key]["name"]})
        reports.append({
            "haven_id": haven_id, "quotes": quotes, "queue_occupied": bool(queue),
            "affordable_count": sum(item["affordable"] for item in quotes),
        })
    return {"havens": reports, "read_only": True, "snapshot": True}
