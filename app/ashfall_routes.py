"""ASHFALL 3.8 — safe, deterministic strategic reconnaissance route planner.

Planning never discovers sectors, launches missions or reveals hidden biome data.
"""
from collections import deque
from app.ashfall_frontier import neighbors, frontier_state

MAX_ROUTE_STEPS = 15

def plan_route(home, target, discovered):
    if any(not (0 <= v < 16) for v in (*home,*target)):
        raise ValueError("Coordinates outside world bounds")
    known = set(discovered) | {home}
    if home == target:
        return {"path":[],"next_sector":None,"unknown_steps":0,"known_steps":0,
                "minimum_seconds":0,"maximum_seconds":0,"status":"home"}
    # Shortest path, breaking ties in favor of already discovered sectors.
    queue = deque([home])
    previous = {home:None}
    while queue:
        current = queue.popleft()
        candidates = sorted(neighbors(*current),key=lambda p:(p not in known,p[1],p[0]))
        for nxt in candidates:
            if nxt in previous:
                continue
            previous[nxt]=current
            if nxt==target:
                queue.clear()
                break
            queue.append(nxt)
    if target not in previous:
        raise ValueError("No route through world")
    path=[]
    node=target
    while node!=home:
        path.append(node)
        node=previous[node]
    path.reverse()
    unknown=[p for p in path if p not in known]
    # Threat is hidden until surveyed; show honest range rather than leaking it.
    # Each unknown step requires a new mission. Each mission's distance is
    # calculated from the Haven, not the previous waypoint.
    minimum=sum(120+45*max(0,max(abs(home[0]-x),abs(home[1]-y))-1) for x,y in unknown)
    maximum=sum(240+45*max(0,max(abs(home[0]-x),abs(home[1]-y))-1) for x,y in unknown)
    return {"path":[{"x":x,"y":y,"known":(x,y) in known} for x,y in path],
            "next_sector":next(({"x":x,"y":y} for x,y in path if (x,y) not in known),None),
            "unknown_steps":len(unknown),"known_steps":len(path)-len(unknown),
            "minimum_seconds":minimum,"maximum_seconds":maximum,
            "status":frontier_state(home,discovered,target)}
