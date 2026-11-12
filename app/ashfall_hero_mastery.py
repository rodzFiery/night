"""ASHFALL 6.2 — persistent hero mastery and distinct combat techniques."""
from fastapi import HTTPException
from app.ashfall_heroes import HEROES

SKILLS={
 "mara":(("Bulwark Discipline","infantry",0.008),("Field Command","all",0.003)),
 "kael":(("Breakthrough Charge","rider",0.008),("Pathfinder Instinct","all",0.003)),
 "nyra":(("Predator Focus","hunter",0.008),("Silent Signals","all",0.003)),
 "orion":(("Last Stand","infantry",0.010),("Sentinel Protocol","all",0.004)),
}
from app.ashfall_hero_generations import CATALOG
for _key,_hero in CATALOG.items():
 if _key not in SKILLS:
  _class=_hero["specialty"]
  SKILLS[_key]=((_hero["title"]+" Doctrine",_class,0.008),
                (_hero["name"].split()[0]+" Resolve","all",0.003))

MAX_LEVEL=10

def initialize(db):
 db.execute("""CREATE TABLE IF NOT EXISTS ashfall_hero_skills(
 haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
 hero_key TEXT NOT NULL,skill_index INTEGER NOT NULL CHECK(skill_index IN (0,1)),
 level INTEGER NOT NULL CHECK(level BETWEEN 1 AND 10),
 PRIMARY KEY(haven_id,hero_key,skill_index))""")

def skill_cost(index,next_level):
 return {"training_manual":next_level*(3 if index==0 else 2),
         "skill_insignia":max(0,next_level-3) if index==0 else max(0,next_level-5)}

def skill_snapshot(db,hid,key,materials=None):
 if key not in HEROES:raise HTTPException(400,"Unknown hero")
 levels={r["skill_index"]:r["level"] for r in db.execute(
  "SELECT skill_index,level FROM ashfall_hero_skills WHERE haven_id=? AND hero_key=?",(hid,key))}
 rankrow=db.execute("SELECT rank FROM ashfall_hero_ranks WHERE haven_id=? AND hero_key=?",(hid,key)).fetchone()
 rank=rankrow[0] if rankrow else 0
 owned=bool(db.execute("SELECT 1 FROM ashfall_heroes WHERE haven_id=? AND hero_key=?",(hid,key)).fetchone())
 result=[]
 for i,(name,specialty,per_level) in enumerate(SKILLS[key]):
  level=levels.get(i,0)
  cost=skill_cost(i,level+1) if level<MAX_LEVEL else None
  required_rank=level//2
  missing={k:max(0,v-(materials or {}).get(k,0)) for k,v in (cost or {}).items()}
  result.append({"index":i,"name":name,"specialty":specialty,"level":level,
    "max_level":MAX_LEVEL,"bonus_percent":round(level*per_level*100,2),
    "next_cost":cost,"required_rank":required_rank,
    "can_upgrade":bool(owned and cost and rank>=required_rank and not any(missing.values())),
    "missing_resources":missing})
 return result

def train(db,hid,key,index):
 if key not in SKILLS or index not in (0,1):raise HTTPException(400,"Unknown skill")
 from app.ashfall_hero_ascension import consume
 materials={r["material"]:r["quantity"] for r in db.execute(
  "SELECT material,quantity FROM ashfall_hero_materials WHERE haven_id=?",(hid,))}
 skills=skill_snapshot(db,hid,key,materials)
 skill=skills[index]
 if skill["next_cost"] is None:raise HTTPException(409,"Skill already mastered")
 if not skill["can_upgrade"]:raise HTTPException(409,"Hero, rank or training resources insufficient")
 for material,amount in skill["next_cost"].items():
  if amount:consume(db,hid,material,amount)
 db.execute("""INSERT INTO ashfall_hero_skills(haven_id,hero_key,skill_index,level)
 VALUES(?,?,?,?) ON CONFLICT(haven_id,hero_key,skill_index)
 DO UPDATE SET level=excluded.level""",(hid,key,index,skill["level"]+1))
 return skill["level"]+1

def combat_bonus(db,hid,key,unit):
 if key not in SKILLS:return 0.0
 if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='ashfall_hero_skills'").fetchone():
  return 0.0
 result=0.0
 for row in db.execute("SELECT skill_index,level FROM ashfall_hero_skills WHERE haven_id=? AND hero_key=?",(hid,key)):
  _,specialty,per_level=SKILLS[key][row["skill_index"]]
  if specialty=="all" or specialty==unit:result+=row["level"]*per_level
 return min(.14,result)
