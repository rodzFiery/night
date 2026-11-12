"""ASHFALL 65 — server-authoritative, permanently earned settlement milestones.

No client-supplied progress, spendable rewards or speculative unlocks.
Awarded records are idempotent and scoped to the owning Haven.
"""
import time

TIERS = (5, 15, 30, 50)
LEGACY_POINTS = {5: 100, 15: 300, 30: 750, 50: 1500}
CHRONICLE = {
    5: ("First Foundations", "The haven establishes its first enduring settlement-wide foundation."),
    15: ("Citadel of Survivors", "Every essential facility rises into a resilient frontier stronghold."),
    30: ("Crystal Frontier", "The entire haven reaches the threshold of advanced frontier architecture."),
    50: ("Eternal Bastion", "Every settlement facility stands among the highest achievements of the frontier."),
}
FACILITIES = ("hq", "farm", "lumber", "salvage", "fuel", "barracks")


def initialize(db):
    db.execute("""CREATE TABLE IF NOT EXISTS ashfall_settlement_achievements(
        haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
        milestone_level INTEGER NOT NULL CHECK(milestone_level IN (5,15,30,50)),
        earned_at REAL NOT NULL,
        PRIMARY KEY(haven_id, milestone_level)
    )""")


def evaluate(db, haven_id, levels, now=None):
    """Award qualifying milestones from trusted server-side building levels only."""
    now = time.time() if now is None else float(now)
    if not all(key in levels for key in FACILITIES):
        raise ValueError("Cannot award settlement milestones from incomplete levels")
    initialize(db)
    lowest = min(max(0, int(levels[key])) for key in FACILITIES)
    for tier in TIERS:
        if lowest >= tier:
            db.execute(
                """INSERT OR IGNORE INTO ashfall_settlement_achievements
                   (haven_id,milestone_level,earned_at) VALUES(?,?,?)""",
                (haven_id, tier, now),
            )
    return status(db, haven_id, levels)


def status(db, haven_id, levels):
    """Return earned records plus truthful progress toward the next threshold."""
    earned = {
        int(row["milestone_level"]): float(row["earned_at"])
        for row in db.execute(
            """SELECT milestone_level,earned_at FROM ashfall_settlement_achievements
               WHERE haven_id=?""", (haven_id,)
        )
    }
    tiers = []
    for tier in TIERS:
        reached = sum(int(levels.get(key, 0)) >= tier for key in FACILITIES)
        tiers.append({
            "level": tier,
            "earned": tier in earned,
            "earned_at": earned.get(tier),
            "reached": reached,
            "total": len(FACILITIES),
            "title": CHRONICLE[tier][0],
            "description": CHRONICLE[tier][1],
            "legacy_points": LEGACY_POINTS[tier],
        })
    history = [
        {"level": tier, "earned_at": earned[tier], "legacy_points": LEGACY_POINTS[tier],
         "title": CHRONICLE[tier][0], "description": CHRONICLE[tier][1]}
        for tier in sorted(earned, key=lambda level: (earned[level], level))
        if tier in LEGACY_POINTS
    ]
    points = sum(item["legacy_points"] for item in history)
    next_tier = next((tier for tier in TIERS if tier not in earned), None)
    return {
        "tiers": tiers,
        "earned_count": len(history),
        "total": len(TIERS),
        "legacy_points": points,
        "max_legacy_points": sum(LEGACY_POINTS.values()),
        "next_legacy_points": LEGACY_POINTS[next_tier] if next_tier else 0,
        "history": history,
    }
