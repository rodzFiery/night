"""ASHFALL 4.1 — Frontier Legacy: earned cartographic progression.

Pure deterministic projections of player-owned discovery data. Milestones
are achievements, not spendable currencies or automatically granted rewards.
"""
from app.ashfall_frontier import WORLD_SECTORS

TIERS = (
    ("WASTELAND INITIATE", 0),
    ("DUST PATHFINDER", 3),
    ("FRONTIER SCOUT", 8),
    ("ASH CARTOGRAPHER", 16),
    ("IRON TRAILBLAZER", 32),
    ("REGIONAL VANGUARD", 64),
    ("WORLD SURVEYOR", 128),
    ("LEGEND OF THE FRONTIER", 255),
)


def legacy_snapshot(home, discovered, mission_count=0):
    """Calculate milestones using unique discoveries, never repeated missions."""
    if not (0 <= home[0] < WORLD_SECTORS and 0 <= home[1] < WORLD_SECTORS):
        raise ValueError("Invalid home sector")
    cells = {(x, y) for x, y in discovered
             if 0 <= x < WORLD_SECTORS and 0 <= y < WORLD_SECTORS}
    cells.discard(home)
    count = len(cells)
    unlocked = [name for name, threshold in TIERS if count >= threshold]
    current = len(unlocked) - 1
    name, floor = TIERS[current]
    next_tier = TIERS[current + 1] if current + 1 < len(TIERS) else None
    return {
        "title": name,
        "rank": current + 1,
        "max_rank": len(TIERS),
        "unique_discoveries": count,
        "completed_expeditions": max(0, int(mission_count)),
        "world_completion_percent": round(100 * (count + 1) / (WORLD_SECTORS ** 2), 2),
        "unlocked_titles": unlocked,
        "next_title": next_tier[0] if next_tier else None,
        "next_threshold": next_tier[1] if next_tier else None,
        "discoveries_remaining": max(0, next_tier[1] - count) if next_tier else 0,
        "tier_progress_percent": min(100, round(100 * (count - floor) /
            (next_tier[1] - floor))) if next_tier else 100,
        "milestones": [
            {"title": title, "required": threshold, "unlocked": count >= threshold}
            for title, threshold in TIERS
        ],
        "note": "Titles are earned from unique charted sectors. They do not yet grant economy or combat bonuses.",
    }
