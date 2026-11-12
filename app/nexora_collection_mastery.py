"""NEXORA 72 — deterministic, non-spendable collection mastery.

Mastery is a read-only classification of earned achievement goals.
It does not mint XP, currency, inventory, unlocks or gameplay advantages.
"""
TIERS = (
    (0, "Uncharted", "Your collection journey has begun."),
    (20, "Pathfinder", "The first discoveries are becoming a legacy."),
    (40, "Wayfinder", "Your accomplishments are gaining momentum."),
    (60, "Vanguard", "Your collection spans meaningful milestones."),
    (80, "Luminary", "Few chapters remain undiscovered."),
    (100, "Chronicle Complete", "Every currently catalogued goal is earned."),
)


def collection_mastery(discovery):
    earned = discovery["earned"]
    total = discovery["total"]
    if type(earned) is not int or type(total) is not int or total < 0 or not 0 <= earned <= total:
        raise ValueError("Invalid achievement collection totals")
    percent = (100 * earned / total) if total else 0
    current_index = max(index for index, tier in enumerate(TIERS) if percent >= tier[0])
    threshold, title, description = TIERS[current_index]
    upcoming = TIERS[current_index + 1] if current_index + 1 < len(TIERS) else None
    if upcoming is None:
        next_goal = None
        needed = 0
    else:
        import math
        next_goal = math.ceil(upcoming[0] * total / 100)
        needed = max(0, next_goal - earned)
    return {
        "rank": current_index,
        "title": title,
        "description": description,
        "earned": earned,
        "total": total,
        "percent": round(percent),
        "next_title": upcoming[1] if upcoming else None,
        "next_threshold": upcoming[0] if upcoming else None,
        "next_goal": next_goal,
        "remaining_to_next": needed,
        "ranks": [
            {
                "title": tier_title,
                "threshold": tier_threshold,
                "achieved": percent >= tier_threshold,
                "required": math.ceil(tier_threshold * total / 100),
            }
            for tier_threshold, tier_title, _ in TIERS
        ],
    }
