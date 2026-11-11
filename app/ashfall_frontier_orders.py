"""ASHFALL 4.2 — Fog-safe frontier strategic recommendations."""
from app.ashfall_frontier import neighbors, WORLD_SECTORS

def frontier_orders(home, discovered, known_profiles, mission=None, objective=None):
    known = set(discovered) | {home}
    reachable = sorted({p for cell in known for p in neighbors(*cell) if p not in known},
                       key=lambda p: (max(abs(p[0]-home[0]), abs(p[1]-home[1])), p[1], p[0]))
    if mission:
        return {"status": "SCOUTS DEPLOYED", "reachable_total": len(reachable),
                "next_action": "Claim the current mission when its timer completes.", "orders": []}
    orders = []
    if objective and tuple(objective) in reachable:
        orders.append({"kind": "OBJECTIVE", "x": objective[0], "y": objective[1],
                       "title": "Advance saved objective",
                       "reason": "Your saved destination is reachable from charted territory."})
    candidate = next((p for p in reachable if not objective or p != tuple(objective)), None)
    if candidate:
        orders.append({"kind": "EXPLORE", "x": candidate[0], "y": candidate[1],
                       "title": "Expand the nearest frontier",
                       "reason": "Adjacent to known territory. Unknown threat and resources remain hidden."})
    resources = {}
    for cell in known:
        profile = known_profiles.get(cell)
        if profile and profile.get("resource_focus"):
            key = profile["resource_focus"]
            resources[key] = resources.get(key, 0) + 1
    if resources:
        resource, count = sorted(resources.items(), key=lambda p: (-p[1], p[0]))[0]
        orders.append({"kind": "INTELLIGENCE", "x": None, "y": None,
                       "title": "Review surveyed resources",
                       "reason": f"{resource.title()} appears in {count} known sectors. This is intelligence, not a production bonus."})
    return {"status": "FRONTIER READY" if reachable else "WORLD CHARTED",
            "reachable_total": len(reachable),
            "next_action": "Select a reachable sector to scout." if reachable else "All sectors have been charted.",
            "orders": orders[:3]}
