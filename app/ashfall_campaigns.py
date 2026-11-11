"""ASHFALL 3.5: deterministic regional exploration campaigns.

Campaign objectives are derived from server-owned discoveries and expedition
history. Completing chapters unlocks narrative records, not spendable rewards.
"""
from collections import Counter
from app.ashfall_world import sector_profile

CAMPAIGNS = (
    ("first_contact", "I · First Contact", "Break the silence beyond your walls",
     (("first_survey", "Complete your first foreign survey", "surveys", 1),
      ("first_return", "Archive a reconnaissance expedition", "missions", 1))),
    ("frontier_network", "II · Frontier Network", "Establish a reliable regional picture",
     (("three_surveys", "Chart three foreign sectors", "surveys", 3),
      ("three_returns", "Record three completed expeditions", "missions", 3),
      ("two_biomes", "Identify two distinct biomes", "biomes", 2))),
    ("wilderness_mastery", "III · Wilderness Mastery", "Master the terrain around your Haven",
     (("five_surveys", "Chart five foreign sectors", "surveys", 5),
      ("three_biomes", "Identify three distinct biomes", "biomes", 3),
      ("high_threat", "Survey a threat level 4+ region", "dangerous", 1))),
    ("regional_atlas", "IV · The Regional Atlas", "Complete your local reconnaissance network",
     (("local_chart", "Survey every neighboring sector", "local", "all"),
      ("eight_returns", "Archive eight reconnaissance expeditions", "missions", 8))),
)

def campaign_snapshot(state_id, home_x, home_y, discoveries, completed_missions):
    seen = {(int(x), int(y)) for x,y in discoveries
            if 0 <= int(x) < 16 and 0 <= int(y) < 16 and (int(x),int(y)) != (home_x,home_y)}
    neighbors = {(x,y) for x in range(max(0,home_x-1),min(15,home_x+1)+1)
                 for y in range(max(0,home_y-1),min(15,home_y+1)+1)
                 if (x,y)!=(home_x,home_y)}
    profiles = [sector_profile(state_id,x,y) for x,y in seen]
    missions = len(set((int(x),int(y)) for x,y in completed_missions))
    metrics = {"surveys":len(seen), "missions":missions,
               "biomes":len(set(p["biome"] for p in profiles)),
               "dangerous":sum(p["threat"]>=4 for p in profiles),
               "local":len(seen & neighbors)}
    chapters=[]
    previous_complete=True
    for key,name,description,objectives in CAMPAIGNS:
        goals=[]
        for code,label,metric,target in objectives:
            required=len(neighbors) if target=="all" else target
            current=min(metrics[metric],required)
            goals.append({"key":code,"label":label,"current":current,
                          "target":required,"complete":current>=required})
        complete=all(g["complete"] for g in goals)
        chapters.append({"key":key,"name":name,"description":description,
                         "unlocked":previous_complete,"complete":complete,
                         "completed_objectives":sum(g["complete"] for g in goals),
                         "total_objectives":len(goals),"objectives":goals})
        previous_complete=previous_complete and complete
    return {"chapters":chapters,
            "completed_chapters":sum(c["complete"] for c in chapters),
            "total_chapters":len(chapters),
            "reward_policy":"Narrative achievements only; no spendable resources or XP"}
