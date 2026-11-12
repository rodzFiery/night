"""NEXORA 71 — discovery catalog for known, server-authoritative achievements.

Catalog entries describe goals, not awards. Only earned provider records establish
completion. Future worlds must register their own trusted catalog entries.
"""
from app.nexora_universal_chronicle import PLATFORM_CATALOG
from app.ashfall_settlement_achievements import CHRONICLE, LEGACY_POINTS, TIERS

PLATFORM_GOALS = {
    "first-arrival": "Create your NEXORA player identity.",
    "first-spark": "Earn your first platform progression.",
    "level-ten": "Reach platform level 10.",
    "thousand-xp": "Accumulate 1,000 lifetime platform XP.",
    "daily-seven": "Earn the seven-day login achievement.",
}


def discovery_catalog():
    catalog = []
    for key, (title, description) in PLATFORM_CATALOG.items():
        catalog.append({
            "key": "nexora:" + key,
            "world": "NEXORA",
            "title": title,
            "description": description,
            "objective": PLATFORM_GOALS.get(key, "Earn this platform achievement."),
            "prestige": 0,
        })
    for tier in TIERS:
        title, description = CHRONICLE[tier]
        catalog.append({
            "key": "ashfall:level:" + str(tier),
            "world": "ASHFALL",
            "title": title,
            "description": description,
            "objective": "Bring all six Haven facilities to level " + str(tier) + ".",
            "prestige": LEGACY_POINTS[tier],
        })
    return catalog


def achievement_discovery(chronicle):
    """Match earned events to known goals without awarding or writing anything.

    ASHFALL may have multiple Havens; a tier is collected once for discovery,
    while its per-Haven achievements remain distinct in the full Chronicle.
    """
    events = chronicle["events"]
    earned_keys = set()
    for event in events:
        if event["world"] == "NEXORA":
            earned_keys.add(event["id"])
        elif event["world"] == "ASHFALL":
            parts = event["id"].split(":")
            if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
                earned_keys.add("ashfall:level:" + parts[2])
    goals = [
        {**entry, "earned": entry["key"] in earned_keys}
        for entry in discovery_catalog()
    ]
    completed = sum(goal["earned"] for goal in goals)
    worlds = []
    for world in ("NEXORA", "ASHFALL"):
        scoped = [goal for goal in goals if goal["world"] == world]
        worlds.append({
            "world": world, "earned": sum(goal["earned"] for goal in scoped),
            "total": len(scoped),
        })
    return {
        "earned": completed,
        "total": len(goals),
        "percent": round(100 * completed / len(goals)) if goals else 0,
        "worlds": worlds,
        "goals": goals,
    }
