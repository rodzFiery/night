"""ASHFALL 8.0 — Grand Arsenal: deterministic, server-owned item catalog and crafting.

Catalog entries are definitions, not automatically owned items. No randomized packs.
Inventory mutations must be called inside a database transaction by API handlers.
"""
from fastapi import HTTPException

RARITIES=("COMMON","UNCOMMON","RARE","EPIC","LEGENDARY","SUPREME")
SLOTS=("head","body","boots","gloves","weapon","artifact")
MATERIALS=("scrap","fabric","alloy","platinum","crystal","relic","core",
 "training_manual","skill_insignia","schematic","refinement_stone","fusion_core",
 "tactical_data","biofiber","reactor_cell","nanoweave","titanium","ceramic",
 "signal_chip","power_coupling")
FAMILIES=("Warden","Nomad","Specter","Titan","Ember","Obsidian","Vanguard",
 "Eclipse","Sovereign","Aether","Sentinel","Ironclad")
CHIEF_SLOTS=("helmet","armor","boots","gloves","weapon","insignia")
CATEGORIES=("hero_gear","chief_gear","charm","material","research","event")

def build_catalog():
 result={}
 for material in MATERIALS:
  result["mat:"+material]={"id":"mat:"+material,"name":material.replace("_"," ").title(),
   "category":"material","rarity":"COMMON","stackable":True,"max_stack":100000000}
 for family in FAMILIES:
  for slot in SLOTS:
   for tier,rarity in enumerate(RARITIES,1):
    key=f"hero:{family.lower()}:{slot}:{tier}"
    result[key]={"id":key,"name":f"{rarity.title()} {family} {slot.title()}",
      "category":"hero_gear","rarity":rarity,"slot":slot,"tier":tier,
      "stackable":False,"max_stack":1}
  for slot in CHIEF_SLOTS:
   for tier,rarity in enumerate(RARITIES,1):
    key=f"chief:{family.lower()}:{slot}:{tier}"
    result[key]={"id":key,"name":f"{rarity.title()} {family} Chief {slot.title()}",
      "category":"chief_gear","rarity":rarity,"slot":slot,"tier":tier,
      "stackable":False,"max_stack":1}
 for family in FAMILIES:
  for rarity in RARITIES:
   for stage in range(1,11):
    key=f"charm:{family.lower()}:{rarity.lower()}:{stage}"
    result[key]={"id":key,"name":f"{family} {rarity.title()} Charm {stage}",
      "category":"charm","rarity":rarity,"stage":stage,
      "stackable":False,"max_stack":1}
 for domain in ("warfare","logistics","medicine","engineering","scouting","defense","economy","communications"):
  for tier in range(1,51):
   key=f"research:{domain}:{tier}"
   result[key]={"id":key,"name":f"{domain.title()} Research File {tier}",
    "category":"research","rarity":RARITIES[min(5,(tier-1)//9)],
    "stackable":True,"max_stack":100000}
 for season in range(1,17):
  for stage in range(1,101):
   key=f"event:season{season:02d}:{stage:02d}"
   result[key]={"id":key,"name":f"Season {season:02d} Salvage Token {stage:02d}",
    "category":"event","rarity":RARITIES[min(5,(stage-1)//9)],
    "stackable":True,"max_stack":100000}
 return result

CATALOG=build_catalog()
assert len(CATALOG)>=3000

def initialize(db):
 db.execute("""CREATE TABLE IF NOT EXISTS ashfall_item_stacks(
  haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
  item_id TEXT NOT NULL,quantity INTEGER NOT NULL CHECK(quantity>=0),
  PRIMARY KEY(haven_id,item_id))""")
 db.execute("""CREATE TABLE IF NOT EXISTS ashfall_item_instances(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
  item_id TEXT NOT NULL,enhancement INTEGER NOT NULL DEFAULT 0
   CHECK(enhancement BETWEEN 0 AND 20),
  equipped_to TEXT,created_at REAL NOT NULL DEFAULT 0)""")
 db.execute("CREATE INDEX IF NOT EXISTS idx_ashfall_item_owner ON ashfall_item_instances(haven_id,item_id)")
 db.execute("""CREATE UNIQUE INDEX IF NOT EXISTS idx_ashfall_unique_equipped
 ON ashfall_item_instances(haven_id,equipped_to)
 WHERE equipped_to IS NOT NULL""")

def definition(item_id):
 item=CATALOG.get(item_id)
 if item is None:raise HTTPException(400,"Unknown arsenal item")
 return item

def balance(db,hid,item_id):
 definition(item_id)
 row=db.execute("SELECT quantity FROM ashfall_item_stacks WHERE haven_id=? AND item_id=?",
                (hid,item_id)).fetchone()
 return row[0] if row else 0

def grant(db,hid,item_id,amount,now=0):
 item=definition(item_id)
 if type(amount) is not int or amount<=0 or amount>1000000:
  raise HTTPException(400,"Invalid item quantity")
 if item["stackable"]:
  if balance(db,hid,item_id)+amount>item["max_stack"]:
   raise HTTPException(409,"Inventory stack limit reached")
  db.execute("""INSERT INTO ashfall_item_stacks(haven_id,item_id,quantity) VALUES(?,?,?)
   ON CONFLICT(haven_id,item_id) DO UPDATE SET quantity=quantity+excluded.quantity""",
   (hid,item_id,amount))
  return {"item_id":item_id,"quantity":amount}
 for _ in range(amount):
  db.execute("INSERT INTO ashfall_item_instances(haven_id,item_id,created_at) VALUES(?,?,?)",
             (hid,item_id,now))
 return {"item_id":item_id,"quantity":amount}

def consume(db,hid,item_id,amount):
 item=definition(item_id)
 if not item["stackable"]:raise HTTPException(400,"Use instance operations for equipment")
 if type(amount) is not int or amount<=0:raise HTTPException(400,"Invalid quantity")
 cursor=db.execute("""UPDATE ashfall_item_stacks SET quantity=quantity-?
 WHERE haven_id=? AND item_id=? AND quantity>=?""",(amount,hid,item_id,amount))
 if cursor.rowcount!=1:raise HTTPException(409,"Insufficient crafting materials")

def recipe(item_id):
 item=definition(item_id)
 if item["category"] not in ("hero_gear","chief_gear","charm"):
  raise HTTPException(400,"Item is not craftable")
 tier=item.get("tier",item.get("stage",1))
 costs={"mat:schematic":tier*2,"mat:alloy":tier*12,
        "mat:refinement_stone":tier*4}
 if tier>=4:costs["mat:crystal"]=tier*3
 if tier>=6:costs["mat:core"]=tier
 return costs

def craft(db,hid,item_id,now=0):
 costs=recipe(item_id)
 # Validate all ingredients before mutating anything; caller commits atomically.
 for ingredient,amount in costs.items():
  if balance(db,hid,ingredient)<amount:
   raise HTTPException(409,"Insufficient "+definition(ingredient)["name"])
 for ingredient,amount in costs.items():consume(db,hid,ingredient,amount)
 return {"crafted":grant(db,hid,item_id,1,now),"costs":costs}

def enhance(db,hid,instance_id):
 row=db.execute("""SELECT id,item_id,enhancement,equipped_to FROM ashfall_item_instances
 WHERE id=? AND haven_id=?""",(instance_id,hid)).fetchone()
 if not row:raise HTTPException(404,"Equipment not found")
 level=row[2]
 if level>=20:raise HTTPException(409,"Maximum enhancement reached")
 cost=(level+1)*5
 consume(db,hid,"mat:refinement_stone",cost)
 db.execute("UPDATE ashfall_item_instances SET enhancement=enhancement+1 WHERE id=? AND haven_id=?",
            (instance_id,hid))
 return {"instance_id":instance_id,"enhancement":level+1,"cost":{"mat:refinement_stone":cost}}

def equip(db,hid,instance_id,target):
 row=db.execute("SELECT item_id FROM ashfall_item_instances WHERE id=? AND haven_id=?",
                (instance_id,hid)).fetchone()
 if not row:raise HTTPException(404,"Equipment not found")
 item=definition(row[0])
 if item["category"] not in ("hero_gear","chief_gear"):
  raise HTTPException(400,"Item cannot be equipped")
 prefix="chief" if item["category"]=="chief_gear" else "hero"
 if not isinstance(target,str) or len(target)>90 or not target.startswith(prefix+":") or not target.endswith(":"+item["slot"]):
  raise HTTPException(400,"Invalid equipment target")
 # The caller must validate the target hero is owned before equipping.
 db.execute("UPDATE ashfall_item_instances SET equipped_to=NULL WHERE haven_id=? AND equipped_to=?",
            (hid,target))
 db.execute("UPDATE ashfall_item_instances SET equipped_to=? WHERE haven_id=? AND id=?",
            (target,hid,instance_id))
 return {"instance_id":instance_id,"target":target}

def inventory(db,hid,category=None,limit=100,offset=0):
 if category is not None and category not in CATEGORIES:raise HTTPException(400,"Unknown category")
 if type(limit) is not int or not 1<=limit<=100 or type(offset) is not int or offset<0:
  raise HTTPException(400,"Invalid pagination")
 stacks=db.execute("""SELECT item_id,quantity FROM ashfall_item_stacks
 WHERE haven_id=? AND quantity>0 ORDER BY item_id""",(hid,)).fetchall()
 instances=db.execute("""SELECT id,item_id,enhancement,equipped_to FROM ashfall_item_instances
 WHERE haven_id=? ORDER BY id""",(hid,)).fetchall()
 records=([{"item":CATALOG[r[0]],"quantity":r[1],"kind":"stack"} for r in stacks if r[0] in CATALOG]
  +[{"instance_id":r[0],"item":CATALOG[r[1]],"enhancement":r[2],
     "equipped_to":r[3],"kind":"equipment"} for r in instances if r[1] in CATALOG])
 if category:records=[r for r in records if r["item"]["category"]==category]
 return {"catalog_size":len(CATALOG),"total_records":len(records),
         "items":records[offset:offset+limit],"limit":limit,"offset":offset}
