"""NEXORA 79 — compact, read-only strategic command overview.

Projects verified collection and Haven reports into a small command surface.
No writes, claims, upgrades, rewards or speculative state transitions.
"""


def strategic_command_overview(discovery, mastery, pursuits, intelligence, roadmap, forecast, readiness):
    earned = discovery["earned"]
    total = discovery["total"]
    if not (type(earned) is int and type(total) is int and 0 <= earned <= total):
        raise ValueError("Invalid collection state")
    by_haven = lambda report: {item["haven_id"]: item for item in report["havens"]}
    roadmaps = by_haven(roadmap)
    forecasts = by_haven(forecast)
    readiness_map = by_haven(readiness)
    haven_id = intelligence["recommended_haven"]
    if haven_id is not None and (haven_id not in roadmaps or haven_id not in forecasts or haven_id not in readiness_map):
        raise ValueError("Strategic reports are inconsistent")
    selected = roadmaps.get(haven_id) if haven_id is not None else None
    selected_forecast = forecasts.get(haven_id) if haven_id is not None else None
    selected_readiness = readiness_map.get(haven_id) if haven_id is not None else None
    next_step = selected["steps"][0] if selected and selected["steps"] else None
    next_quote = None
    next_economy = None
    if next_step:
        key = next_step["key"]
        next_quote = next((item for item in selected_forecast["quotes"] if item["key"] == key), None)
        next_economy = next((item for item in selected_readiness["quotes"] if item["key"] == key), None)
        if next_quote is None or next_economy is None:
            raise ValueError("Recommended facility is missing a resource quote")
    first_pursuit = pursuits["pursuits"][0] if pursuits["pursuits"] else None
    return {
        "collection": {
            "earned": earned, "total": total, "percent": discovery["percent"],
            "rank": mastery["title"],
        },
        "pursuit": {
            "title": first_pursuit["title"], "world": first_pursuit["world"],
            "objective": first_pursuit["objective"],
        } if first_pursuit else None,
        "settlement": {
            "haven_id": haven_id, "title": selected["title"],
            "percent": selected["progress_percent"],
            "remaining_levels": selected["remaining_levels"],
        } if selected else None,
        "upgrade": {
            "name": next_step["name"], "next_level": next_step["next_level"],
            "affordable": next_quote["affordable"],
            "status": next_economy["status"],
            "estimated_hours": next_economy["estimated_hours"],
            "limiting_resource": next_economy["limiting_resource"],
        } if next_step else None,
        "havens_count": intelligence["haven_count"],
        "read_only": True,
    }
