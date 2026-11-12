"""ASHFALL 7.1 — earnable hero operation challenges.

Challenge completion is derived from persisted event and battle records.
Claiming rewards is idempotent per Haven, UTC period and operation.
"""
from datetime import datetime,timezone
from fastapi import HTTPException

OPERATIONS={
 "daily_scout":{"name":"Frontier Recovery","period":"daily","events":2,
                "rewards":{"training_manual":6,"scrap":15}},
 "weekly_campaign":{"name":"War Council Campaign","period":"weekly","victories":3,
                    "rewards":{"skill_insignia":3,"alloy":25,"gold_fragment":5}},
 "weekly_explorer":{"name":"Relic Expedition","period":"weekly","events":8,
                    "rewards":{"relic":12,"crystal":12,"gold_fragment":4}},
}

def initialize(db):
 db.execute("""CREATE TABLE IF NOT EXISTS ashfall_hero_operation_claims(
 haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
 operation TEXT NOT NULL,period TEXT NOT NULL,claimed_at REAL NOT NULL,
 PRIMARY KEY(haven_id,operation,period))""")

def period_bounds(now,kind):
 dt=datetime.fromtimestamp(now,timezone.utc)
 day=datetime(dt.year,dt.month,dt.day,tzinfo=timezone.utc).timestamp()
 if kind=="daily":return day,day+86400
 start=day-dt.weekday()*86400
 return start,start+7*86400

def status(db,hid,now):
 result=[]
 for key,definition in OPERATIONS.items():
  start,end=period_bounds(now,definition["period"])
  count=0
  table="ashfall_event_claims" if "events" in definition else "ashfall_battle_reports"
  exists=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(table,)).fetchone()
  if exists and "events" in definition:
   count=db.execute("""SELECT COUNT(*) FROM ashfall_event_claims
    WHERE haven_id=? AND claimed_at>=? AND claimed_at<?""",(hid,start,end)).fetchone()[0]
  elif exists:
   count=db.execute("""SELECT COUNT(*) FROM ashfall_battle_reports
    WHERE haven_id=? AND outcome='victory' AND created_at>=? AND created_at<?""",
    (hid,start,end)).fetchone()[0]
  target=definition.get("events",definition.get("victories"))
  period=datetime.fromtimestamp(start,timezone.utc).strftime("%Y-%m-%d")
  claimed=bool(db.execute("""SELECT 1 FROM ashfall_hero_operation_claims
   WHERE haven_id=? AND operation=? AND period=?""",(hid,key,period)).fetchone())
  result.append({"key":key,"name":definition["name"],"period":definition["period"],
    "progress":min(count,target),"target":target,"claimed":claimed,
    "ready":count>=target and not claimed,"rewards":definition["rewards"],
    "reset_at":end})
 return result

def claim(db,hid,key,now):
 if key not in OPERATIONS:raise HTTPException(400,"Unknown operation")
 operation=next(x for x in status(db,hid,now) if x["key"]==key)
 if operation["claimed"]:raise HTTPException(409,"Operation reward already claimed")
 if not operation["ready"]:raise HTTPException(409,"Operation objective incomplete")
 start,_=period_bounds(now,operation["period"])
 period=datetime.fromtimestamp(start,timezone.utc).strftime("%Y-%m-%d")
 inserted=db.execute("""INSERT OR IGNORE INTO ashfall_hero_operation_claims
 (haven_id,operation,period,claimed_at) VALUES(?,?,?,?)""",(hid,key,period,now))
 if inserted.rowcount!=1:raise HTTPException(409,"Already claimed")
 from app.ashfall_hero_ascension import grant
 for material,quantity in operation["rewards"].items():grant(db,hid,material,quantity)
 return operation["rewards"]
