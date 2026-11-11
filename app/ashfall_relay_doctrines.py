"""ASHFALL 5.2 — permanent, resource-backed relay specialization.

A level-two operational relay can commit to one doctrine. The decision is
per Haven, state and theater, permanent, and charged atomically.
"""
import time
from fastapi import HTTPException, Request
from app.ashfall_economy import accrue
from app.ashfall_relay_upgrades import effective_level

DOCTRINES={
    "SURVEY":{"label":"Deep Survey","description":"+4 percentage points to local scouting speed.","cost":{"wood":240,"metal":160,"gas":75}},
    "SIGNAL":{"label":"Signal Command","description":"+2 percentage points locally; another +3 when connected to an adjacent operational relay.","cost":{"wood":180,"metal":240,"gas":100}},
}

def doctrine_bonus(doctrine,linked):
    if doctrine=="SURVEY":return 4
    if doctrine=="SIGNAL":return 5 if linked else 2
    return 0

def doctrine_for(db,haven_id,state_id,x,y):
    row=db.execute("""SELECT doctrine FROM ashfall_relay_doctrines
        WHERE haven_id=? AND state_id=? AND theater_x=? AND theater_y=?""",
        (haven_id,state_id,x,y)).fetchone()
    return row[0] if row else None

def doctrine_snapshot(db,haven_id,state_id,now,balances=None):
    from app.ashfall_relay_upgrades import upgrade_status
    relays=upgrade_status(db,haven_id,state_id,now)
    choices=[]
    for relay in relays:
        x,y=relay["theater_x"],relay["theater_y"]
        chosen=doctrine_for(db,haven_id,state_id,x,y)
        eligible=relay["relay_operational"] and relay["level"]>=2 and not relay["upgrading"]
        options=[]
        for key,definition in DOCTRINES.items():
            cost=definition["cost"]
            missing={k:max(0,v-(balances or {}).get(k,0)) for k,v in cost.items()} if balances is not None else {}
            options.append({"key":key,"label":definition["label"],"description":definition["description"],
                            "cost":cost,"missing_resources":missing,
                            "can_choose":bool(eligible and not chosen and not any(missing.values()))})
        choices.append({"id":relay["id"],"theater_x":x,"theater_y":y,
                        "level":relay["level"],"selected":chosen,
                        "eligible":bool(eligible and not chosen),
                        "options":options})
    return choices

def register_relay_doctrines(app,database,get_user,valid_csrf):
    with database() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS ashfall_relay_doctrines(
            haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
            state_id INTEGER NOT NULL,
            theater_x INTEGER NOT NULL CHECK(theater_x BETWEEN 0 AND 3),
            theater_y INTEGER NOT NULL CHECK(theater_y BETWEEN 0 AND 3),
            doctrine TEXT NOT NULL CHECK(doctrine IN ('SURVEY','SIGNAL')),
            chosen_at REAL NOT NULL,
            PRIMARY KEY(haven_id,state_id,theater_x,theater_y))""")

    def owner(db,request,state_id):
        user=get_user(request.session.get("user_id"))
        if not user:raise HTTPException(401,"Sign in required")
        row=db.execute("SELECT id FROM ashfall_havens WHERE user_id=? AND state_id=?",
                       (user["id"],state_id)).fetchone()
        if not row:raise HTTPException(404,"Haven not found")
        return row["id"]

    @app.get("/ashfall/api/atlas/relay-doctrines")
    async def get_doctrines(request:Request,state_id:int=1):
        from app.ashfall_economy import snapshot
        with database() as db:
            hid=owner(db,request,state_id)
            db.execute("BEGIN IMMEDIATE")
            now=time.time()
            balances=snapshot(db,hid,now)["resources"]
            return {"doctrines":doctrine_snapshot(db,hid,state_id,now,balances),
                    "permanent_choice":True,"server_time":now}

    @app.post("/ashfall/api/atlas/relay-doctrines/choose")
    async def choose_doctrine(request:Request):
        form=await request.form()
        if not valid_csrf(request,str(form.get("csrf_token",""))):
            raise HTTPException(400,"Invalid security token")
        try:
            state_id=int(form.get("state_id","1"))
            x=int(form.get("theater_x","-1"))
            y=int(form.get("theater_y","-1"))
        except (TypeError,ValueError):
            raise HTTPException(400,"Invalid theater coordinates")
        key=str(form.get("doctrine","")).upper()
        if not (0<=x<4 and 0<=y<4) or key not in DOCTRINES:
            raise HTTPException(400,"Invalid doctrine or theater")
        with database() as db:
            db.execute("BEGIN IMMEDIATE")
            hid=owner(db,request,state_id)
            now=time.time()
            relay=db.execute("""SELECT finishes_at FROM ashfall_theater_relays
                WHERE haven_id=? AND state_id=? AND theater_x=? AND theater_y=?""",
                (hid,state_id,x,y)).fetchone()
            if not relay or relay["finishes_at"]>now:
                raise HTTPException(409,"Operational relay required")
            upgrade=db.execute("""SELECT level,finishes_at FROM ashfall_relay_upgrades
                WHERE haven_id=? AND state_id=? AND theater_x=? AND theater_y=?""",
                (hid,state_id,x,y)).fetchone()
            if not upgrade or effective_level(upgrade,now)<2:
                raise HTTPException(409,"Relay level two required")
            if upgrade["finishes_at"] is not None and upgrade["finishes_at"]>now:
                raise HTTPException(409,"Finish the current upgrade first")
            if doctrine_for(db,hid,state_id,x,y):
                raise HTTPException(409,"Doctrine already selected")
            accrue(db,hid,now)
            cost=DOCTRINES[key]["cost"]
            balance=db.execute("SELECT wood,metal,gas FROM ashfall_resource_balances WHERE haven_id=?",
                               (hid,)).fetchone()
            if not balance or any(balance[k]<v for k,v in cost.items()):
                raise HTTPException(409,"Insufficient doctrine resources")
            db.execute("""UPDATE ashfall_resource_balances
                SET wood=wood-?,metal=metal-?,gas=gas-? WHERE haven_id=?""",
                (cost["wood"],cost["metal"],cost["gas"],hid))
            db.execute("""INSERT INTO ashfall_relay_doctrines
                (haven_id,state_id,theater_x,theater_y,doctrine,chosen_at)
                VALUES(?,?,?,?,?,?)""",(hid,state_id,x,y,key,now))
            return {"selected":key,"theater_x":x,"theater_y":y,"cost":cost}
