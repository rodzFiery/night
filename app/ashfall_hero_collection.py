"""ASHFALL 7.2 — persistent hero collection chronicles.

Claimable one-time milestones reward long-term collection progression.
All thresholds are checked against server-side owned heroes, rank and gear.
"""
from fastapi import HTTPException

MILESTONES=(
 ("first_blood","First Arrival",1,{"training_manual":10,"scrap":20}),
 ("vanguard","The Vanguard",5,{"gold_fragment":10,"alloy":20}),
 ("warband","A Growing Warband",10,{"gold_fragment":25,"crystal":15}),
 ("legion","Legion of Ash",25,{"gold_fragment":50,"relic":25}),
 ("dynasty","Dynasty of Heroes",50,{"gold_fragment":100,"core":20}),
 ("empire","An Empire of Legends",100,{"gold_fragment":200,"core":50}),
 ("eternal","The Eternal Roster",160,{"gold_fragment":400,"core":100}),
)

def initialize(db):
 db.execute("""CREATE TABLE IF NOT EXISTS ashfall_hero_collection_claims(
 haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
 milestone TEXT NOT NULL, claimed_at REAL NOT NULL,
 PRIMARY KEY(haven_id,milestone))""")

def snapshot(db,hid):
 owned=db.execute("SELECT COUNT(*) FROM ashfall_heroes WHERE haven_id=?",(hid,)).fetchone()[0]
 ranks=db.execute("SELECT COALESCE(SUM(rank),0) FROM ashfall_hero_ranks WHERE haven_id=?",(hid,)).fetchone()[0]
 gear=db.execute("SELECT COUNT(*) FROM ashfall_hero_gear WHERE haven_id=?",(hid,)).fetchone()[0]
 claimed={r[0] for r in db.execute("SELECT milestone FROM ashfall_hero_collection_claims WHERE haven_id=?",(hid,))}
 return {"owned":owned,"total":160,"ranks_earned":ranks,"equipment_crafted":gear,
  "completion_percent":round(owned/160*100,2),
  "milestones":[{"key":key,"name":name,"required":threshold,"progress":min(owned,threshold),
    "claimed":key in claimed,"ready":owned>=threshold and key not in claimed,"rewards":rewards}
    for key,name,threshold,rewards in MILESTONES]}

def claim(db,hid,key,now):
 entry=next((m for m in snapshot(db,hid)["milestones"] if m["key"]==key),None)
 if entry is None:raise HTTPException(400,"Unknown collection milestone")
 if entry["claimed"]:raise HTTPException(409,"Milestone already claimed")
 if not entry["ready"]:raise HTTPException(409,"Milestone not completed")
 result=db.execute("""INSERT OR IGNORE INTO ashfall_hero_collection_claims(haven_id,milestone,claimed_at)
 VALUES(?,?,?)""",(hid,key,now))
 if result.rowcount!=1:raise HTTPException(409,"Milestone already claimed")
 from app.ashfall_hero_ascension import grant
 for material,amount in entry["rewards"].items():grant(db,hid,material,amount)
 return entry["rewards"]
