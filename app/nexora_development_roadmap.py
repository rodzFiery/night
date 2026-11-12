"""NEXORA 76 — deterministic settlement development roadmap.

Advisory sequencing based on authoritative persisted facility levels.
Never queues construction, estimates costs without a game quote, or grants rewards.
"""
from app.ashfall_settlement_achievements import FACILITIES

# Strategic order resolves ties only. Lowest-level facilities are prioritized
# first to remove settlement-wide milestone bottlenecks.
TIE_ORDER = {key: index for index, key in enumerate(FACILITIES)}
DISPLAY = {
    "hq": "Command Center", "farm": "Farm", "lumber": "Lumber Yard",
    "salvage": "Salvage Station", "fuel": "Fuel Collector",
    "barracks": "Barracks",
}


def development_roadmap(intelligence, limit=6):
    if type(limit) is not int or not 1 <= limit <= len(FACILITIES):
        raise ValueError("Invalid roadmap limit")
    havens = intelligence["havens"]
    roadmap = []
    for haven in havens:
        if haven["complete"]:
            roadmap.append({
                "haven_id": haven["haven_id"], "complete": True,
                "title": haven["title"], "target_level": None,
                "steps": [], "remaining_levels": 0, "ready": len(FACILITIES),
                "total": len(FACILITIES), "progress_percent": 100,
            })
            continue
        target = haven["target_level"]
        facilities = haven["facilities"]
        if type(target) is not int or target < 1:
            raise ValueError("Invalid settlement target")
        if len(facilities) != len(FACILITIES) or {f["key"] for f in facilities} != set(FACILITIES):
            raise ValueError("Incomplete settlement facility state")
        for facility in facilities:
            if type(facility["level"]) is not int or facility["level"] < 0:
                raise ValueError("Invalid facility level")
        ordered = sorted(
            (facility for facility in facilities if facility["level"] < target),
            key=lambda facility: (facility["level"], TIE_ORDER[facility["key"]]),
        )
        steps = [{
            "priority": index,
            "key": facility["key"],
            "name": DISPLAY[facility["key"]],
            "current": facility["level"],
            "next_level": facility["level"] + 1,
            "target": target,
            "remaining": target - facility["level"],
            "reason": "Lowest-level facility bottleneck" if index == 1 else "Settlement-wide milestone requirement",
        } for index, facility in enumerate(ordered[:limit], 1)]
        completed_levels = sum(min(facility["level"], target) for facility in facilities)
        required_levels = target * len(FACILITIES)
        roadmap.append({
            "haven_id": haven["haven_id"], "complete": False,
            "title": haven["title"], "target_level": target,
            "steps": steps,
            "remaining_levels": required_levels - completed_levels,
            "ready": sum(facility["level"] >= target for facility in facilities),
            "total": len(FACILITIES),
            "progress_percent": round(100 * completed_levels / required_levels),
        })
    return {
        "havens": roadmap,
        "recommended_haven": intelligence["recommended_haven"],
        "advisory": True,
        "no_automatic_construction": True,
    }
