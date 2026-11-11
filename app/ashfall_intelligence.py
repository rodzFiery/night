"""ASHFALL 4.0 — fog-safe operational frontier intelligence.

All metrics derive from a player's own charted sectors. No unseen biome,
threat, resource or faction information is exposed.
"""
from collections import Counter
from app.ashfall_frontier import neighbors, WORLD_SECTORS


def frontier_intelligence(home, discovered, known_profiles):
    known = set(discovered) | {home}
    available = set()
    for x, y in known:
        for target in neighbors(x, y):
            if target not in known:
                available.add(target)
    biomes = Counter()
    resources = Counter()
    threat_total = 0
    for cell in known:
        profile = known_profiles.get(cell)
        if not profile:
            continue
        biomes[profile["biome"]] += 1
        resources[profile["resource_focus"]] += 1
        threat_total += profile["threat"]
    surveyed = sum(biomes.values())
    max_sectors = WORLD_SECTORS * WORLD_SECTORS
    return {
        "charted": len(known),
        "world_total": max_sectors,
        "world_percent": round(100 * len(known) / max_sectors, 2),
        "reachable": len(available),
        "biomes": dict(sorted(biomes.items())),
        "resource_focus": dict(sorted(resources.items())),
        "average_known_threat": round(threat_total / surveyed, 2) if surveyed else None,
        "charted_with_intelligence": surveyed,
        "next_frontier": [{"x": x, "y": y} for x, y in sorted(available, key=lambda p: (p[1], p[0]))],
    }
