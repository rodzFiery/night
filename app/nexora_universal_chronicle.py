"""NEXORA 69 — universal, read-only achievement projection.

Each world owns its authoritative achievement ledger. NEXORA only composes
validated, account-scoped records; it never grants rewards or accepts client claims.
"""
from datetime import datetime, timezone
from app.ashfall_settlement_achievements import player_chronicle

PLATFORM_CATALOG = {
    "first-arrival": ("First Arrival", "Established a NEXORA player identity."),
    "first-spark": ("First Spark", "Earned your first platform progression."),
    "level-ten": ("Level Ten", "Reached NEXORA level ten."),
    "thousand-xp": ("Thousand XP", "Earned one thousand lifetime XP."),
    "daily-seven": ("Seven Day Streak", "Completed a seven-day login streak."),
}


def normalize_timestamp(value):
    """Normalize a trusted timestamp for stable cross-world ordering."""
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), timezone.utc).isoformat()
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat()
    raise ValueError("Unsupported achievement timestamp")


def universal_chronicle(db, user_id):
    """Aggregate only achievements already earned by this account."""
    platform = db.execute(
        """SELECT achievement_key,unlocked_at FROM player_achievements
           WHERE user_id=? ORDER BY unlocked_at,achievement_key""", (user_id,)
    ).fetchall()
    events = []
    for record in platform:
        key = str(record["achievement_key"])
        title, description = PLATFORM_CATALOG.get(
            key, (key.replace("-", " ").title(), "NEXORA platform achievement.")
        )
        events.append({
            "id": "nexora:" + key,
            "world": "NEXORA",
            "title": title,
            "description": description,
            "earned_at": normalize_timestamp(record["unlocked_at"]),
            "prestige": 0,
        })
    ashfall = player_chronicle(db, user_id)
    for record in ashfall["history"]:
        events.append({
            "id": f"ashfall:{record['haven_id']}:{record['level']}",
            "world": "ASHFALL",
            "title": record["title"],
            "description": record["description"],
            "earned_at": normalize_timestamp(record["earned_at"]),
            "prestige": record["legacy_points"],
        })
    events.sort(key=lambda item: (item["earned_at"], item["world"], item["id"]))
    return {
        "total_earned": len(events),
        "platform_earned": sum(event["world"] == "NEXORA" for event in events),
        "world_earned": sum(event["world"] != "NEXORA" for event in events),
        "ashfall_prestige": ashfall["legacy_points"],
        "events": events,
    }
