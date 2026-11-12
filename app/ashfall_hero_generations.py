"""ASHFALL 7.0 — sixteen collectible hero generations (160 original heroes).

Release progression is server-authoritative: the first generation is available;
each two DISTINCT weekly event-cache claims unlock the next generation.
"""
from datetime import datetime,timezone

GENERATIONS=16
PER_GENERATION=10
RARITY_ORDER=("NORMAL","EPIC","LEGENDARY","SUPREME")
FIRST=("Mara","Kael","Nyra","Orion","Vera","Dax","Iris","Riven","Sable","Atlas")
LAST=("Voss","Rourke","Vale","Ash","Kestrel","Forge","Hale","Drake","Wren","Stone")
PREFIX=("Ashen","Iron","Storm","Ember","Obsidian","Radiant","Warden","Crimson",
        "Titan","Spectral","Eclipse","Aether","Vanguard","Sovereign","Celestial","Eternal")
CLASS=("infantry","rider","hunter")
RARITY_BY_POSITION=("NORMAL","NORMAL","NORMAL","EPIC","EPIC","EPIC",
                    "LEGENDARY","LEGENDARY","LEGENDARY","SUPREME")
STATS=("march_capacity","attack","defense","health","infantry_attack",
       "infantry_defense","rider_attack","rider_defense","hunter_attack",
       "hunter_defense","infected_defense","dash_health","dash_attack","dash_defense")

def catalog():
 heroes={}
 for generation in range(1,GENERATIONS+1):
  for index in range(PER_GENERATION):
   key=("mara","kael","nyra","orion")[index] if generation==1 and index<4 else f"g{generation:02d}h{index+1:02d}"
   rarity=("NORMAL","EPIC","LEGENDARY","SUPREME")[index] if generation==1 and index<4 else RARITY_BY_POSITION[index]
   specialty=CLASS[(generation+index)%3]
   name=f"{FIRST[index]} {LAST[(index+generation-1)%10]}"
   if generation==1 and index<4:name=("Mara Voss","Kael Rourke","Nyra Vale","Orion Ash")[index]
   heroes[key]={"key":key,"name":name,"title":f"{PREFIX[generation-1]} {('Vanguard','Pathfinder','Watcher','Sentinel','Nomad','Engineer','Ranger','Breaker','Oracle','Marshal')[index]}",
      "generation":generation,"position":index+1,"rarity":rarity,
      "specialty":specialty,"bonus":(.10,.14,.18,.22)[RARITY_ORDER.index(rarity)],
      "cost":{},"hq":1}
 assert len(heroes)==160
 return heroes

CATALOG=catalog()

def released_generation(db,hid):
 # Each two completed weekly event cycles advance the collection by one generation.
 count=db.execute("""SELECT COUNT(*) FROM ashfall_hero_reward_claims
 WHERE haven_id=? AND kind='weekly'""",(hid,)).fetchone()[0]
 return min(GENERATIONS,1+count//2)

def is_released(db,hid,key):
 hero=CATALOG.get(key)
 return bool(hero and hero["generation"]<=released_generation(db,hid))

def stats(key,level=0,rank=0,gear=None,skills=None):
 hero=CATALOG[key]
 rarity=RARITY_ORDER.index(hero["rarity"])
 gen=hero["generation"]
 gear_points=sum(("BASIC","NORMAL","EPIC","PLATINUM","DIAMOND","LEGENDARY","SUPREME").index(v)+1
                 for v in (gear or {}).values() if v)
 skill_points=sum(s.get("level",0) for s in (skills or []))
 base=30+rarity*24+gen*8+level*3+rank*19+gear_points*7+skill_points*5
 primary=hero["specialty"]
 return {
  "march_capacity":int(250+gen*70+level*18+rank*125+gear_points*35),
  "attack":base,
  "defense":int(base*.86),
  "health":int(base*11),
  "infantry_attack":round((base/18)*(1.7 if primary=="infantry" else .65),2),
  "infantry_defense":round((base/21)*(1.7 if primary=="infantry" else .65),2),
  "rider_attack":round((base/18)*(1.7 if primary=="rider" else .65),2),
  "rider_defense":round((base/21)*(1.7 if primary=="rider" else .65),2),
  "hunter_attack":round((base/18)*(1.7 if primary=="hunter" else .65),2),
  "hunter_defense":round((base/21)*(1.7 if primary=="hunter" else .65),2),
  "infected_defense":round(base/24,2),
  "dash_health":int(base*9),
  "dash_attack":int(base*.65),
  "dash_defense":int(base*.57),
 }
