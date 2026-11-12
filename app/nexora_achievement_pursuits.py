"""NEXORA 74 — server-derived Achievement Pursuit recommendations.

Pursuits are planning suggestions, not claims or rewards. Source-of-truth
achievement status always comes from the universal Chronicle projection.
"""
from app.ashfall_settlement_achievements import TIERS


def achievement_pursuits(discovery, limit=3):
    """Select realistic next goals without fabricating partial progress."""
    if type(limit) is not int or not 1 <= limit <= 12:
        raise ValueError("Invalid pursuit limit")
    goals = discovery["goals"]
    pending = [goal for goal in goals if not goal["earned"]]
    # Settlement milestones must be pursued in ascending order; recommend
    # only the first unearned ASHFALL tier, not every late-game tier at once.
    ashfall = [
        goal for goal in pending
        if goal["world"] == "ASHFALL"
        and goal["key"].startswith("ashfall:level:")
        and goal["key"].rsplit(":", 1)[-1].isdigit()
    ]
    ashfall.sort(key=lambda goal: int(goal["key"].rsplit(":", 1)[-1]))
    next_ashfall = ashfall[0] if ashfall else None
    platform = [goal for goal in pending if goal["world"] == "NEXORA"]
    # First Arrival and First Spark are introductory goals; level and XP
    # milestones follow, then the seven-day streak.
    priorities = {
        "nexora:first-arrival": 0,
        "nexora:first-spark": 1,
        "nexora:level-ten": 2,
        "nexora:thousand-xp": 3,
        "nexora:daily-seven": 4,
    }
    platform.sort(key=lambda goal: (priorities.get(goal["key"], 100), goal["key"]))
    selected = []
    # Interleave one milestone from each connected source when possible.
    if platform:
        selected.append(platform.pop(0))
    if next_ashfall:
        selected.append(next_ashfall)
    selected.extend(platform)
    selected = selected[:limit]
    pursuits = []
    for index, goal in enumerate(selected, 1):
        pursuits.append({
            "key": goal["key"],
            "world": goal["world"],
            "title": goal["title"],
            "objective": goal["objective"],
            "priority": index,
            "destination": "/ashfall" if goal["world"] == "ASHFALL" else "/dashboard",
            "note": (
                "The next unearned settlement-wide tier; progress depends on all six Haven facilities."
                if goal["world"] == "ASHFALL"
                else "Earned status is verified by NEXORA's server-side achievement ledger."
            ),
        })
    return {
        "pursuits": pursuits,
        "remaining": len(pending),
        "complete": not pending,
        "advisory": True,
    }
