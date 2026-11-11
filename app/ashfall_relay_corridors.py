"""ASHFALL 4.9 — connected relay corridors and expansion opportunities.

Only operational installations and charted theaters are considered.
No unseen sector intelligence is exposed.
"""
from collections import deque

def relay_corridors(online, charted_theaters):
    online=set(online)
    charted=set(charted_theaters)
    def neighbors(cell):
        x,y=cell
        return {(a,b) for a,b in ((x-1,y),(x+1,y),(x,y-1),(x,y+1))
                if 0<=a<4 and 0<=b<4}
    remaining=set(online)
    corridors=[]
    while remaining:
        start=min(remaining,key=lambda p:(p[1],p[0]))
        queue=deque([start]);remaining.remove(start);component=[]
        while queue:
            cell=queue.popleft();component.append(cell)
            for candidate in sorted(neighbors(cell)&remaining,key=lambda p:(p[1],p[0])):
                remaining.remove(candidate);queue.append(candidate)
        corridors.append(sorted(component,key=lambda p:(p[1],p[0])))
    corridors.sort(key=lambda c:(-len(c),c[0][1],c[0][0]))
    opportunities=[]
    for cell in sorted(charted-online,key=lambda p:(p[1],p[0])):
        links=len(neighbors(cell)&online)
        if links:
            opportunities.append({"theater_x":cell[0],"theater_y":cell[1],
                                  "id":f"T-{cell[0]+1}{cell[1]+1}",
                                  "adjacent_operational_relays":links,
                                  "priority":"HIGH" if links>=2 else "STANDARD"})
    opportunities.sort(key=lambda p:(-p["adjacent_operational_relays"],p["theater_y"],p["theater_x"]))
    return {"corridor_count":len(corridors),
            "largest_corridor_size":max((len(c) for c in corridors),default=0),
            "corridors":[{"size":len(c),"theaters":[f"T-{x+1}{y+1}" for x,y in c]}
                         for c in corridors],
            "expansion_opportunities":opportunities[:8],
            "note":"Opportunities require surveyed theaters; links are orthogonal and based on completed installations only."}
