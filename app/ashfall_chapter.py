"""ASHFALL 0.5: chapter-two construction quests, claim-once rewards, Haven XP."""
import time
from fastapi import HTTPException, Request
from app.ashfall_economy import snapshot as economy_snapshot

QUESTS=(
 ("farm","Fields of Tomorrow","Restore the Farm","farm",1,{"food":300,"wood":180},100),
 ("lumber","Timber for the Walls","Restore the Lumber Yard","lumber",1,{"food":250,"metal":80},120),
 ("salvage","Steel from the Ashes","Restore the Salvage Station","salvage",1,{"wood":300,"metal":120},140),
 ("fuel","Keep the Fires Burning","Restore the Fuel Collector","fuel",1,{"food":350,"gas":80},160),
 ("command","A Stronger Haven","Upgrade Command Center to Level 2","hq",2,{"food":500,"wood":500,"metal":200},250),
)
RES=("food","wood","metal","gas")
def initialize(db):
    db.execute("""CREATE TABLE IF NOT EXISTS ashfall_quest_claims(
      haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
      quest_key TEXT NOT NULL, claimed_at REAL NOT NULL,
      PRIMARY KEY(haven_id,quest_key))""")
    db.execute("""CREATE TABLE IF NOT EXISTS ashfall_haven_progression(
      haven_id INTEGER PRIMARY KEY REFERENCES ashfall_havens(id) ON DELETE CASCADE,
      xp INTEGER NOT NULL DEFAULT 0 CHECK(xp>=0) )""")

def level_for(xp):
    level=1
    while level<100 and xp>=100*level*(level+1)//2:level+=1
    return level

def data(db,hid,now):
    econ=economy_snapshot(db,hid,now)
    claimed={r["quest_key"] for r in db.execute("SELECT quest_key FROM ashfall_quest_claims WHERE haven_id=?",(hid,))}
    row=db.execute("SELECT xp FROM ashfall_haven_progression WHERE haven_id=?",(hid,)).fetchone()
    xp=row["xp"] if row else 0
    quests=[]
    for key,title,objective,building,target,reward,xp_reward in QUESTS:
        completed=econ["buildings"][building]["level"]>=target
        quests.append({"key":key,"title":title,"objective":objective,"target_level":target,
          "building":building,"completed":completed,"claimed":key in claimed,"reward":reward,"xp_reward":xp_reward})
    level=level_for(xp)
    return {"quests":quests,"xp":xp,"level":level,"next_level_xp":100*level*(level+1)//2 if level<100 else None,
            "all_claimed":all(q["claimed"] for q in quests),"resources":econ["resources"]}

def register_chapter(app,database,get_user,valid_csrf):
    with database() as db:initialize(db)
    def own(db,uid,state):
        row=db.execute("SELECT id FROM ashfall_havens WHERE user_id=? AND state_id=?",(uid,state)).fetchone()
        if not row:raise HTTPException(404,"Haven not found in this state")
        return row["id"]

    @app.get("/ashfall/api/chapter2")
    async def chapter_status(request:Request,state_id:int=1):
        user=get_user(request.session.get("user_id"))
        if not user:raise HTTPException(401,"Sign in required")
        with database() as db:return data(db,own(db,user["id"],state_id),time.time())

    @app.post("/ashfall/api/chapter2/claim")
    async def claim(request:Request):
        user=get_user(request.session.get("user_id"))
        if not user:raise HTTPException(401,"Sign in required")
        form=await request.form()
        if not valid_csrf(request,str(form.get("csrf_token",""))):raise HTTPException(400,"Security token invalid")
        key=str(form.get("quest",""))
        try:state=int(form.get("state_id","1"))
        except (ValueError,TypeError):raise HTTPException(400,"Invalid state")
        quest=next((q for q in QUESTS if q[0]==key),None)
        if not quest:raise HTTPException(400,"Unknown quest")
        now=time.time()
        with database() as db:
            # Acquire write lock before checking and awarding to avoid concurrent double claims.
            db.execute("INSERT OR IGNORE INTO ashfall_haven_progression(haven_id,xp) SELECT id,0 FROM ashfall_havens WHERE user_id=? AND state_id=?",(user["id"],state))
            hid=own(db,user["id"],state)
            status=data(db,hid,now)
            target=next(q for q in status["quests"] if q["key"]==key)
            if target["claimed"]:raise HTTPException(409,"Already claimed")
            if not target["completed"]:raise HTTPException(409,"Complete construction first")
            inserted=db.execute("INSERT OR IGNORE INTO ashfall_quest_claims(haven_id,quest_key,claimed_at) VALUES(?,?,?)",(hid,key,now))
            if inserted.rowcount!=1:raise HTTPException(409,"Already claimed")
            reward=quest[5]
            db.execute("UPDATE ashfall_resource_balances SET food=food+?,wood=wood+?,metal=metal+?,gas=gas+? WHERE haven_id=?",
                       (*(reward.get(r,0) for r in RES),hid))
            db.execute("UPDATE ashfall_haven_progression SET xp=xp+? WHERE haven_id=?",(quest[6],hid))
            result=data(db,hid,now)
            result["claimed_title"]=quest[1]
            return result
