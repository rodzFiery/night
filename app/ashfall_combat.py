"""ASHFALL 0.9 — server-authoritative abstract PvE encounters and battle reports."""
import hashlib
import time
from fastapi import HTTPException, Request
from app.ashfall_expeditions import snapshot as expedition_snapshot
from app.ashfall_heroes import bonus_for, award_xp
from app.ashfall_battle_engine import resolve

STATS={"infantry":{"power":4,"guard":5},"rider":{"power":6,"guard":3},"hunter":{"power":7,"guard":2}}
ENCOUNTERS=(
 ("camp_1","Abandoned Outpost",1,28,{"food":120,"wood":90},75),
 ("camp_2","Contested Supply Cache",2,75,{"metal":100,"food":180},120),
 ("camp_3","Wilderness Stronghold",3,150,{"metal":180,"gas":65},200),
)
RES=("food","wood","metal","gas")

def initialize(db):
    db.execute("""CREATE TABLE IF NOT EXISTS ashfall_battle_reports(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
      encounter_key TEXT NOT NULL,
      unit_key TEXT NOT NULL, deployed INTEGER NOT NULL, returned INTEGER NOT NULL,
      outcome TEXT NOT NULL CHECK(outcome IN ('victory','defeat')),
      player_power INTEGER NOT NULL, opponent_power INTEGER NOT NULL,
      reward_food INTEGER NOT NULL DEFAULT 0,reward_wood INTEGER NOT NULL DEFAULT 0,
      reward_metal INTEGER NOT NULL DEFAULT 0,reward_gas INTEGER NOT NULL DEFAULT 0,
      xp_reward INTEGER NOT NULL DEFAULT 0,created_at REAL NOT NULL)""")
    db.execute("CREATE INDEX IF NOT EXISTS idx_ashfall_battle_reports_haven ON ashfall_battle_reports(haven_id,id)")

def encounters(hid):
    result=[]
    for key,name,tier,strength,rewards,xp in ENCOUNTERS:
        digest=hashlib.sha256(f"ashfall:encounter:{hid}:{key}".encode()).digest()
        result.append({"key":key,"name":name,"tier":tier,"strength":strength,
          "x":int.from_bytes(digest[:2],"big")%35-17,"y":int.from_bytes(digest[2:4],"big")%35-17,
          "reward":rewards,"xp":xp})
    return result

def snapshot(db,hid,now):
    expedition=expedition_snapshot(db,hid,now)
    reports=db.execute("""SELECT id,encounter_key,unit_key,deployed,returned,outcome,player_power,
      opponent_power,reward_food,reward_wood,reward_metal,reward_gas,xp_reward,created_at
      FROM ashfall_battle_reports WHERE haven_id=? ORDER BY id DESC LIMIT 15""",(hid,)).fetchall()
    return {"encounters":encounters(hid),"reports":[dict(r) for r in reports],
            "troops_available":expedition["troops_available"],"server_time":now}

def register_combat(app,database,get_user,valid_csrf):
    with database() as db:initialize(db)
    def own(db,uid,state):
        row=db.execute("SELECT id FROM ashfall_havens WHERE user_id=? AND state_id=?",(uid,state)).fetchone()
        if not row:raise HTTPException(404,"Haven not found")
        return row["id"]

    @app.get("/ashfall/api/combat")
    async def combat_status(request:Request,state_id:int=1):
        user=get_user(request.session.get("user_id"))
        if not user:raise HTTPException(401,"Sign in required")
        with database() as db:return snapshot(db,own(db,user["id"],state_id),time.time())

    @app.post("/ashfall/api/combat/engage")
    async def engage(request:Request):
        user=get_user(request.session.get("user_id"))
        if not user:raise HTTPException(401,"Sign in required")
        form=await request.form()
        if not valid_csrf(request,str(form.get("csrf_token",""))):raise HTTPException(400,"Security token invalid")
        key=str(form.get("encounter",""))
        unit=str(form.get("unit",""))
        try:state=int(form.get("state_id","1"));quantity=int(form.get("quantity","0"))
        except (ValueError,TypeError):raise HTTPException(400,"Invalid encounter request")
        if unit not in STATS or not 1<=quantity<=1000:raise HTTPException(400,"Invalid troop selection")
        now=time.time()
        with database() as db:
            hid=own(db,user["id"],state)
            current=snapshot(db,hid,now)
            target=next((e for e in current["encounters"] if e["key"]==key),None)
            if not target:raise HTTPException(400,"Unknown encounter")
            if current["troops_available"].get(unit,0)<quantity:raise HTTPException(409,"Not enough available troops")
            hq=db.execute("SELECT command_center_level FROM ashfall_havens WHERE id=?",(hid,)).fetchone()["command_center_level"]
            if hq<target["tier"]:raise HTTPException(409,"Command Center level too low")
            # Stable, transparent PvE formula: no randomized loot or hidden stat modifiers.
            from app.ashfall_hero_warfare import battle_attributes
            attributes=battle_attributes(db,hid,unit)
            try:
                outcome=resolve(quantity,unit,target["strength"],bonus_for(db,hid,unit),attributes)
            except ValueError as exc:
                raise HTTPException(409,str(exc)) from exc
            power=outcome["player_power"]
            opponent=outcome["opponent_power"]
            victory=outcome["victory"]
            loss=outcome["losses"]
            returned=outcome["returned"]
            reward=target["reward"] if victory else {}
            xp=target["xp"] if victory else 0
            db.execute("UPDATE ashfall_troops SET quantity=quantity-? WHERE haven_id=? AND unit_key=?",(loss,hid,unit))
            db.execute("UPDATE ashfall_resource_balances SET food=food+?,wood=wood+?,metal=metal+?,gas=gas+? WHERE haven_id=?",
                       (*(reward.get(r,0) for r in RES),hid))
            if xp:
                db.execute("INSERT OR IGNORE INTO ashfall_haven_progression(haven_id,xp) VALUES(?,0)",(hid,))
                db.execute("UPDATE ashfall_haven_progression SET xp=xp+? WHERE haven_id=?",(xp,hid))
                award_xp(db,hid,xp)
            db.execute("""INSERT INTO ashfall_battle_reports(
              haven_id,encounter_key,unit_key,deployed,returned,outcome,player_power,opponent_power,
              reward_food,reward_wood,reward_metal,reward_gas,xp_reward,created_at)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
              (hid,key,unit,quantity,returned,"victory" if victory else "defeat",power,opponent,
               *(reward.get(r,0) for r in RES),xp,now))
            return snapshot(db,hid,now)
