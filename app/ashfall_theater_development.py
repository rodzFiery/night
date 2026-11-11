"""ASHFALL 4.4 — theater development doctrines.

Advisory, fog-safe strategic plans based on charted intelligence. No automatic
construction, resource consumption, territorial claims or hidden-map access.
"""
DOCTRINES = {
    "SURVEY": {"name": "Cartographic Expansion", "description": "Map the theater before committing resources."},
    "LOGISTICS": {"name": "Supply Corridor", "description": "Plan a future supply route through known terrain."},
    "INDUSTRY": {"name": "Industrial Prospecting", "description": "Prioritize further surveys around known resource patterns."},
    "SECURITY": {"name": "Defensive Reconnaissance", "description": "Study known threats before future defensive investments."},
}

def theater_development(theaters):
    plans = []
    for theater in theaters:
        charted = theater["charted"]
        total = theater["total"]
        threat = theater["average_known_threat"]
        resource = theater["known_resource_focus"]
        if charted == 0:
            doctrine, rationale = "SURVEY", "No reliable intelligence yet. Survey this theater before selecting a specialization."
        elif threat is not None and threat >= 4:
            doctrine, rationale = "SECURITY", "Known threat averages at least 4/5; further reconnaissance should precede investment."
        elif charted < total // 2:
            doctrine, rationale = "SURVEY", "Fewer than half of the sectors have been charted."
        elif resource:
            doctrine, rationale = "INDUSTRY", f"Surveyed sectors suggest {resource} potential; production is not yet affected."
        else:
            doctrine, rationale = "LOGISTICS", "Survey coverage supports planning future regional connections."
        plans.append({
            "id": theater["id"], "doctrine": doctrine,
            "name": DOCTRINES[doctrine]["name"],
            "description": DOCTRINES[doctrine]["description"],
            "rationale": rationale,
            "charted": charted, "total": total,
            "remaining_to_chart": total - charted,
            "readiness_percent": theater["completion_percent"],
            "advisory_only": True,
        })
    return {
        "doctrines": DOCTRINES,
        "plans": plans,
        "note": "Development doctrines are strategic recommendations, not built facilities, ownership, buffs or spendable resources.",
    }
