"""ASHFALL 4.3 — Regional Theaters, fog-safe 4x4 strategic districts.

Each theater aggregates only charted cells. Unknown terrain stays classified.
This is a read-only strategic layer, not territorial ownership.
"""
from collections import Counter
from app.ashfall_frontier import WORLD_SECTORS

THEATER_SIZE = 4

def theater_snapshot(home, discovered, known_profiles):
    known = set(discovered) | {home}
    theaters = []
    for ty in range(0, WORLD_SECTORS, THEATER_SIZE):
        for tx in range(0, WORLD_SECTORS, THEATER_SIZE):
            cells = {(x,y) for y in range(ty,ty+THEATER_SIZE) for x in range(tx,tx+THEATER_SIZE)}
            charted = cells & known
            profiles = [known_profiles[p] for p in sorted(charted) if p in known_profiles]
            resources = Counter(p["resource_focus"] for p in profiles)
            biomes = Counter(p["biome"] for p in profiles)
            threat = round(sum(p["threat"] for p in profiles)/len(profiles),2) if profiles else None
            dominant_resource = sorted(resources.items(),key=lambda a:(-a[1],a[0]))[0][0] if resources else None
            dominant_biome = sorted(biomes.items(),key=lambda a:(-a[1],a[0]))[0][0] if biomes else None
            theaters.append({
                "id": f"T-{tx//THEATER_SIZE+1}{ty//THEATER_SIZE+1}",
                "name": f"THEATER {tx//THEATER_SIZE+1:02d}-{ty//THEATER_SIZE+1:02d}",
                "origin": {"x":tx,"y":ty},
                "charted":len(charted),"total":len(cells),
                "completion_percent":round(100*len(charted)/len(cells)),
                "status":"SECURED INTELLIGENCE" if len(charted)==len(cells) else
                         "UNSURVEYED" if not charted else "PARTIALLY CHARTED",
                "known_resource_focus":dominant_resource,
                "known_biome":dominant_biome,
                "average_known_threat":threat,
                "contains_home":home in cells
            })
    return {"grid_size":4,"theater_size":THEATER_SIZE,"theaters":theaters,
            "note":"Theater status reflects cartographic coverage, not military control. Unknown regions reveal no attributes."}
