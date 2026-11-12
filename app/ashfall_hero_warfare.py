"""ASHFALL 7.1: signature doctrines and six-piece armory synergy.

All calculations use owned, persisted equipment and hero ranks.
No randomness, no purchases, no client-trusted stats.
"""
from app.ashfall_hero_generations import CATALOG

SLOTS=("head","body","boots","gloves","weapon","artifact")
DOCTRINES={
 "infantry":("Iron Bastion",.012),
 "rider":("Thunder Pursuit",.012),
 "hunter":("Deadeye Protocol",.012),
}
RARITY_MULTIPLIER={"NORMAL":1,"EPIC":1.2,"LEGENDARY":1.5,"SUPREME":1.8}
GENERATION_TITLES=("First Arrival","Iron Dawn","Stormfront","Emberfall",
 "Obsidian Watch","Radiant March","Warden's Oath","Crimson Signal",
 "Titan's Stand","Spectral Horizon","Eclipse Protocol","Aether Vanguard",
 "Sovereign Guard","Celestial Front","Eternal Watch","Last Dominion")
CLASS_SIGNATURES={
 "infantry":("Iron Bastion","Bulwark","Citadel"),
 "rider":("Thunder Pursuit","Overdrive","Tempest"),
 "hunter":("Deadeye Protocol","Ghostline","Eagle Eye"),
}
def signature_identity(hero):
 """Deterministic class + generation signature; no paid or random power."""
 gen=hero["generation"]
 class_name=hero["specialty"]
 title=CLASS_SIGNATURES[class_name][(gen-1)//6]
 return {"name":title+" · "+GENERATION_TITLES[gen-1],
         "tier":1+(gen-1)//6,"generation":gen,
         "description":{"infantry":"Strengthens infantry formation combat.",
          "rider":"Strengthens rider strike formations.",
          "hunter":"Strengthens hunter precision formations."}[class_name]}


def snapshot(db,hid,key):
 if key not in CATALOG:return {"signature":None,"set_count":0,"set_bonus_percent":0,"signature_bonus_percent":0}
 hero=CATALOG[key]
 rows=db.execute("SELECT slot,tier FROM ashfall_hero_gear WHERE haven_id=? AND hero_key=?",(hid,key)).fetchall()
 equipped={r["slot"]:r["tier"] for r in rows if r["slot"] in SLOTS}
 count=len(equipped)
 set_bonus=(.015 if count>=3 else 0)+(.03 if count>=6 else 0)
 rankrow=db.execute("SELECT rank FROM ashfall_hero_ranks WHERE haven_id=? AND hero_key=?",(hid,key)).fetchone()
 rank=rankrow[0] if rankrow else 0
 name,base=DOCTRINES[hero["specialty"]]
 identity=signature_identity(hero)
 signature=round(base*RARITY_MULTIPLIER[hero["rarity"]]*(1+rank/10)*(1+min(0.3,(hero["generation"]-1)*0.02)),6)
 return {"signature":identity["name"],"signature_tier":identity["tier"],
         "signature_description":identity["description"],"specialty":hero["specialty"],
         "signature_bonus_percent":round(signature*100,2),
         "set_count":count,"set_bonus_percent":round(set_bonus*100,2),
         "set_progress":{"three_piece":count>=3,"six_piece":count>=6},
         "equipped_slots":list(equipped)}

def tactical_bonus(db,hid,key,unit):
 if key not in CATALOG:return 0.0
 if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='ashfall_hero_gear'").fetchone():
  return 0.0
 owned=db.execute("SELECT 1 FROM ashfall_heroes WHERE haven_id=? AND hero_key=?",(hid,key)).fetchone()
 if not owned:return 0.0
 data=snapshot(db,hid,key)
 return round(data["set_bonus_percent"]/100+
   (data["signature_bonus_percent"]/100 if unit==data["specialty"] else 0),6)

def battle_attributes(db,hid,unit):
 """Live battle attributes from assigned hero; no client-supplied power."""
 if unit not in ("infantry","rider","hunter"):return {"attack":0,"defense":0,"health":0,"march_capacity":0}
 if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='ashfall_hero_assignments'").fetchone():
  return {"attack":0,"defense":0,"health":0,"march_capacity":0}
 row=db.execute("SELECT hero_key FROM ashfall_hero_assignments WHERE haven_id=?",(hid,)).fetchone()
 if not row or row["hero_key"] not in CATALOG:return {"attack":0,"defense":0,"health":0,"march_capacity":0}
 key=row["hero_key"]
 if not db.execute("SELECT 1 FROM ashfall_heroes WHERE haven_id=? AND hero_key=?",(hid,key)).fetchone():
  return {"attack":0,"defense":0,"health":0,"march_capacity":0}
 from app.ashfall_hero_generations import stats
 from app.ashfall_heroes import hero_level
 hero=db.execute("SELECT xp FROM ashfall_heroes WHERE haven_id=? AND hero_key=?",(hid,key)).fetchone()
 rank=db.execute("SELECT rank FROM ashfall_hero_ranks WHERE haven_id=? AND hero_key=?",(hid,key)).fetchone()
 gear={r["slot"]:("BASIC","NORMAL","EPIC","PLATINUM","DIAMOND","LEGENDARY","SUPREME")[r["tier"]]
       for r in db.execute("SELECT slot,tier FROM ashfall_hero_gear WHERE haven_id=? AND hero_key=?",(hid,key))}
 skills=[{"level":r["level"]} for r in db.execute("SELECT level FROM ashfall_hero_skills WHERE haven_id=? AND hero_key=?",(hid,key))]
 s=stats(key,hero_level(hero["xp"]),rank["rank"] if rank else 0,gear,skills)
 return {"attack":s[unit+"_attack"],"defense":s[unit+"_defense"],
         "health":s["health"],"march_capacity":s["march_capacity"]}
