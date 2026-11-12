"""NEXORA 78 — economic readiness intelligence for quoted ASHFALL upgrades.

Read-only instantaneous rates from ASHFALL's production model. Estimates assume
constant production and no spending, queues, research, doctrine or alliance changes.
They are not promised construction completion times.
"""
import time
from app.ashfall_economy import BUILDINGS, RES, production_breakdown


def economic_readiness(db, user_id, forecast):
    owned = {int(row["id"]) for row in db.execute(
        "SELECT id FROM ashfall_havens WHERE user_id=?", (user_id,)
    )}
    havens = []
    for haven in forecast["havens"]:
        hid = int(haven["haven_id"])
        if hid not in owned:
            raise ValueError("Foreign Haven in forecast")
        levels = {row["building_key"]: int(row["level"]) for row in db.execute(
            "SELECT building_key,level FROM ashfall_building_levels WHERE haven_id=?", (hid,)
        )}
        levels = {key: levels.get(key, 0) for key in BUILDINGS}
        # Use the current wall clock for modifiers, but do not advance the economy.
        rates = production_breakdown(db, hid, levels, time.time())
        resources = [{
            "key": resource,
            "per_hour": float(rates.get(resource, {}).get("per_hour", 0)),
            "facility": rates.get(resource, {}).get("facility"),
        } for resource in RES]
        per_hour = {item["key"]: item["per_hour"] for item in resources}
        quotes = []
        for quote in haven["quotes"]:
            missing = quote["shortages"]
            waits = []
            impossible = []
            for resource, amount in missing.items():
                rate = per_hour.get(resource, 0)
                if rate <= 0:
                    impossible.append(resource)
                else:
                    waits.append(amount / rate)
            # Rates for separate resources accumulate concurrently.
            # This is a lower-bound style estimate, not a schedule or guarantee.
            hours = max(waits, default=0)
            if impossible:
                eta = None
                status = "production_unavailable"
            elif quote["blocked"]:
                eta = None
                status = "prerequisite_blocked"
            elif quote["rare_shortages"]:
                eta = None
                status = "rare_material_shortage"
            elif not missing:
                eta = 0
                status = "resources_ready"
            else:
                eta = round(hours, 2)
                status = "production_estimate"
            quotes.append({
                "key": quote["key"], "name": quote["name"],
                "status": status, "estimated_hours": eta,
                "unproducible": impossible,
                "limiting_resource": max(
                    (resource for resource in missing if per_hour.get(resource, 0) > 0),
                    key=lambda resource: missing[resource] / per_hour[resource],
                    default=None,
                ),
                "shortages": dict(missing),
                "rare_shortages": dict(quote["rare_shortages"]),
                "blocked": list(quote["blocked"]),
            })
        havens.append({
            "haven_id": hid, "resources": resources, "quotes": quotes,
            "queue_occupied": haven["queue_occupied"],
        })
    return {
        "havens": havens,
        "read_only": True,
        "assumption": "Constant current production; no spending or game-state changes.",
    }
