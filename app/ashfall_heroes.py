"""ASHFALL 1.0: persistent hero roster, assignments, progression and combat specialties."""
import time
from fastapi import HTTPException, Request
from app.ashfall_economy import snapshot as economy_snapshot

HEROES={
 "mara":{"name":"Mara Voss","title":"The Vanguard","specialty":"infantry","bonus":0.12,"cost":{"food":300,"metal":120},"hq":1},
 "kael":{"name":"Kael Rourke","title":"The Pathfinder","specialty":"rider","bonus":0.15,"cost":{"food":400,"wood":200,"metal":100},"hq":2},
 "nyra":{"name":"Nyra Vale","title":"The Watcher","specialty":"hunter","bonus":0.18,"cost":{"food":450,"metal":200,"gas":50},"hq":3},
 "orion":{"name":"Orion Ash","title":"The Last Sentinel","specialty":"infantry","bonus":0.22,"cost":{"food":750,"metal":400,"gas":150},"hq":4},
}
# Extended catalog keeps original hero identities and adds 156 collectible characters.
from app.ashfall_hero_generations import CATALOG
for _key,_hero in CATALOG.items():
    if _key not in HEROES:
        HEROES[_key]={k:_hero[k] for k in ("name","title","specialty","bonus","cost","hq")}

RES=("food","wood","metal","gas")

def initialize(db):
    db.execute("""CREATE TABLE IF NOT EXISTS ashfall_heroes(
      haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
      hero_key TEXT NOT NULL, xp INTEGER NOT NULL DEFAULT 0 CHECK(xp>=0),
      recruited_at REAL NOT NULL,PRIMARY KEY(haven_id,hero_key))""")
    db.execute("""CREATE TABLE IF NOT EXISTS ashfall_hero_assignments(
      haven_id INTEGER PRIMARY KEY REFERENCES ashfall_havens(id) ON DELETE CASCADE,
      hero_key TEXT NOT NULL)""")

def hero_level(xp):
    level=1
    while level<50 and xp>=75*level*(level+1)//2:level+=1
    return level

def assigned(db,hid):
    row=db.execute("SELECT hero_key FROM ashfall_hero_assignments WHERE haven_id=?",(hid,)).fetchone()
    if not row:return None
    hero=db.execute("SELECT xp FROM ashfall_heroes WHERE haven_id=? AND hero_key=?",(hid,row["hero_key"])).fetchone()
    if not hero or row["hero_key"] not in HEROES:return None
    return row["hero_key"],hero_level(hero["xp"])

def ascension_combat_bonus(db,hid,hero_key):
    """Rank and gear contribute to the existing assigned-hero battle modifier.

    Rank: +0.5 percentage points each (max 5).
    Gear: +0.2 percentage points per completed tier per slot (max 4.2).
    """
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='ashfall_hero_ranks'").fetchone():
        return 0.0
    row=db.execute("SELECT rank FROM ashfall_hero_ranks WHERE haven_id=? AND hero_key=?",
                   (hid,hero_key)).fetchone()
    rank=row[0] if row else 0
    total=0
    if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='ashfall_hero_gear'").fetchone():
        for gear in db.execute("SELECT tier FROM ashfall_hero_gear WHERE haven_id=? AND hero_key=?",
                               (hid,hero_key)):
            total+=gear[0]+1
    return min(0.092,rank*0.005+total*0.002)

def bonus_for(db,hid,unit):
    current=assigned(db,hid)
    if not current:return 0.0
    key,level=current
    hero=HEROES[key]
    base=min(.65,hero["bonus"]+0.02*(level-1)) if hero["specialty"]==unit else min(.25,.04+.01*(level-1))
    from app.ashfall_hero_mastery import combat_bonus
    return min(.85,base+ascension_combat_bonus(db,hid,key)+combat_bonus(db,hid,key,unit))

def award_xp(db,hid,amount):
    current=assigned(db,hid)
    if current and amount>0:
        db.execute("UPDATE ashfall_heroes SET xp=xp+? WHERE haven_id=? AND hero_key=?",(amount,hid,current[0]))

def snapshot(db,hid,now):
    economy=economy_snapshot(db,hid,now)
    owned={r["hero_key"]:r["xp"] for r in db.execute("SELECT hero_key,xp FROM ashfall_heroes WHERE haven_id=?",(hid,))}
    current=assigned(db,hid)
    result={}
    for key,hero in HEROES.items():
        xp=owned.get(key,0)
        level=hero_level(xp)
        result[key]={"name":hero["name"],"title":hero["title"],"specialty":hero["specialty"],
          "recruited":key in owned,"xp":xp,"level":level,
          "next_level_xp":75*level*(level+1)//2 if level<50 else None,
          "specialty_bonus_percent":round(100*min(.65,hero["bonus"]+.02*(level-1))),
          "cost":hero["cost"],"requires_hq":hero["hq"],
          "unlocked":economy["buildings"]["hq"]["level"]>=hero["hq"]}
    return {"heroes":result,"assigned":current[0] if current else None,"resources":economy["resources"]}

def register_heroes(app,database,get_user,valid_csrf):
    with database() as db:initialize(db)
    def own(db,uid,state):
        row=db.execute("SELECT id FROM ashfall_havens WHERE user_id=? AND state_id=?",(uid,state)).fetchone()
        if not row:raise HTTPException(404,"Haven not found")
        return row["id"]

    @app.get("/ashfall/api/heroes")
    async def hero_status(request:Request,state_id:int=1):
        user=get_user(request.session.get("user_id"))
        if not user:raise HTTPException(401,"Sign in required")
        with database() as db:return snapshot(db,own(db,user["id"],state_id),time.time())

    @app.post("/ashfall/api/heroes/action")
    async def hero_action(request:Request):
        user=get_user(request.session.get("user_id"))
        if not user:raise HTTPException(401,"Sign in required")
        form=await request.form()
        if not valid_csrf(request,str(form.get("csrf_token",""))):raise HTTPException(400,"Invalid security token")
        key=str(form.get("hero",""))
        action=str(form.get("action",""))
        if key not in HEROES or action not in ("recruit","assign"):raise HTTPException(400,"Invalid hero action")
        try:state=int(form.get("state_id","1"))
        except (ValueError,TypeError):raise HTTPException(400,"Invalid state")
        with database() as db:
            hid=own(db,user["id"],state)
            status=snapshot(db,hid,time.time())
            hero=status["heroes"][key]
            if action=="recruit":
                raise HTTPException(409,"Recruit heroes with 10 fragments in Hero Command")
                if hero["recruited"]:raise HTTPException(409,"Hero already recruited")
                if not hero["unlocked"]:raise HTTPException(409,"Command Center level too low")
                cost=hero["cost"]
                if any(status["resources"][r]<v for r,v in cost.items()):raise HTTPException(409,"Insufficient resources")
                db.execute("UPDATE ashfall_resource_balances SET food=food-?,wood=wood-?,metal=metal-?,gas=gas-? WHERE haven_id=?",
                           (*(cost.get(r,0) for r in RES),hid))
                db.execute("INSERT INTO ashfall_heroes(haven_id,hero_key,xp,recruited_at) VALUES(?,?,0,?)",(hid,key,time.time()))
            else:
                if not hero["recruited"]:raise HTTPException(409,"Recruit hero first")
                db.execute("INSERT OR REPLACE INTO ashfall_hero_assignments(haven_id,hero_key) VALUES(?,?)",(hid,key))
            return snapshot(db,hid,time.time())
