"""ASHFALL 3.3 — cartographer mastery from durable discovery records.

Mastery is read-only and deterministic. It does not award spendable currencies.
"""
from collections import Counter
from app.ashfall_world import sector_profile

MILESTONES = (
    (1, "First Signal", "Survey your first foreign sector"),
    (3, "Pathfinder", "Record three foreign sectors"),
    (5, "Wasteland Navigator", "Record five foreign sectors"),
    (8, "Regional Cartographer", "Chart all eight neighboring sectors"),
)
BIOME_BADGES = (
    ("Ash Wastes", "Ashwalker"),
    ("Ironwood", "Ironwood Scout"),
    ("Glass Barrens", "Glass Surveyor"),
    ("Frostline", "Frostline Observer"),
    ("Broken Lowlands", "Lowlands Pathfinder"),
    ("Ember Fields", "Ember Cartographer"),
)

def mastery_snapshot(state_id, home_x, home_y, discoveries):
    """Calculate permanent exploration progression without trusting client input."""
    seen = set(discoveries)
    seen.discard((home_x, home_y))
    local = {(x, y) for x in range(max(0, home_x-1), min(15, home_x+1)+1)
             for y in range(max(0, home_y-1), min(15, home_y+1)+1)
             if (x,y) != (home_x,home_y)}
    local_seen = seen & local
    counts = Counter(sector_profile(state_id,x,y)["biome"] for x,y in seen
                     if 0 <= x < 16 and 0 <= y < 16)
    badges = [
        {"key": "milestone_"+str(required), "name": name, "description": description,
         "earned": len(seen) >= required, "progress": min(len(seen),required),
         "target": required}
        for required,name,description in MILESTONES
    ]
    badges.extend(
        {"key": "biome_"+biome.lower().replace(" ","_"), "name": name,
         "description": "Survey a sector in "+biome,
         "earned": counts[biome] > 0, "progress": min(counts[biome],1),
         "target": 1}
        for biome,name in BIOME_BADGES
    )
    return {
        "rank": ("Regional Cartographer" if len(local_seen)==len(local)
                 else "Wasteland Navigator" if len(seen)>=5
                 else "Pathfinder" if len(seen)>=3
                 else "Scout" if len(seen)>=1 else "Uncharted"),
        "surveyed_total": len(seen),
        "local_surveyed": len(local_seen),
        "local_total": len(local),
        "local_percent": round(100*len(local_seen)/len(local)) if local else 100,
        "biome_counts": dict(counts),
        "badges": badges,
        "next_milestone": next((b for b in badges[:len(MILESTONES)] if not b["earned"]),None),
        "rewards": "Cosmetic achievement records only; no resource or XP payouts",
    }
