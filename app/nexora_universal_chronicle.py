"""NEXORA 69 — universal, read-only achievement projection.

Each world owns its authoritative achievement ledger. NEXORA only composes
validated, account-scoped records; it never grants rewards or accepts client claims.
"""
from app.nexora_achievement_providers import compose_chronicle, normalize_timestamp
from app.ashfall_settlement_achievements import player_chronicle

PLATFORM_CATALOG = {
    "first-arrival": ("First Arrival", "Established a NEXORA player identity."),
    "first-spark": ("First Spark", "Earned your first platform progression."),
    "level-ten": ("Level Ten", "Reached NEXORA level ten."),
    "thousand-xp": ("Thousand XP", "Earned one thousand lifetime XP."),
    "daily-seven": ("Seven Day Streak", "Completed a seven-day login streak."),
}


def platform_events(db, user_id):
    """Built-in platform provider; reads only achievements owned by user_id."""
    rows = db.execute(
        """SELECT achievement_key,unlocked_at FROM player_achievements
           WHERE user_id=? ORDER BY unlocked_at,achievement_key""", (user_id,)
    ).fetchall()
    events = []
    for record in rows:
        key = str(record["achievement_key"])
        title, description = PLATFORM_CATALOG.get(
            key, (key.replace("-", " ").title(), "NEXORA platform achievement.")
        )
        events.append({
            "id": "nexora:" + key,
            "world": "NEXORA",
            "title": title,
            "description": description,
            "earned_at": record["unlocked_at"],
            "prestige": 0,
        })
    return events


def ashfall_events(db, user_id):
    """ASHFALL provider; game-owned ledger remains the source of truth."""
    history = player_chronicle(db, user_id)["history"]
    return [{
        "id": f"ashfall:{record['haven_id']}:{record['level']}",
        "world": "ASHFALL",
        "title": record["title"],
        "description": record["description"],
        "earned_at": record["earned_at"],
        "prestige": record["legacy_points"],
    } for record in history]


def universal_chronicle(db, user_id):
    """Compose approved game providers without awarding or duplicating progress."""
    events = compose_chronicle(
        db, user_id,
        (("NEXORA", platform_events), ("ASHFALL", ashfall_events)),
    )
    return {
        "total_earned": len(events),
        "platform_earned": sum(event["world"] == "NEXORA" for event in events),
        "world_earned": sum(event["world"] != "NEXORA" for event in events),
        "ashfall_prestige": sum(
            event["prestige"] for event in events if event["world"] == "ASHFALL"
        ),
        "events": events,
    }
