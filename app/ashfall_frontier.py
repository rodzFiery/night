"""ASHFALL 3.6 — server-authoritative connected exploration frontier."""
WORLD_SECTORS = 16

def neighbors(x, y):
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < WORLD_SECTORS and 0 <= ny < WORLD_SECTORS:
                yield nx, ny

def frontier_state(home, discovered, target):
    """A new sector must touch a known sector, including the home sector."""
    x, y = target
    if not (0 <= x < WORLD_SECTORS and 0 <= y < WORLD_SECTORS):
        return "invalid"
    known = set(discovered) | {home}
    if target in known:
        return "discovered"
    if not any(cell in known for cell in neighbors(x, y)):
        return "locked"
    return "available"

def frontier_window(home, discovered, radius=3):
    """Fixed-size view; exploration beyond this window remains possible via API."""
    hx, hy = home
    known = set(discovered) | {home}
    return [
        {"x": x, "y": y, "status": frontier_state(home, known, (x,y))}
        for y in range(max(0, hy-radius), min(WORLD_SECTORS-1,hy+radius)+1)
        for x in range(max(0, hx-radius), min(WORLD_SECTORS-1,hx+radius)+1)
    ]

def travel_duration(threat, home, target):
    """Scouting travel grows with distance; server computes all timings."""
    distance = max(abs(home[0]-target[0]), abs(home[1]-target[1]))
    return 90 + 30 * threat + 45 * max(0, distance-1)

def atlas_viewport(center_x, center_y, radius=3):
    """Bounded camera window, including sectors at the edges of the world."""
    if not (0 <= center_x < WORLD_SECTORS and 0 <= center_y < WORLD_SECTORS):
        raise ValueError("Atlas camera outside world bounds")
    return [(x,y)
            for y in range(max(0,center_y-radius),min(WORLD_SECTORS-1,center_y+radius)+1)
            for x in range(max(0,center_x-radius),min(WORLD_SECTORS-1,center_x+radius)+1)]
