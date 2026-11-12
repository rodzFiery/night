"""ASHFALL 47 — SQLite integration checks for offline doctrine mastery.

Runs against the actual accrue/snapshot engine with isolated in-memory tables.
No production accounts, network services, or migrations are modified.
"""
import sqlite3
from unittest.mock import patch
from app import ashfall_economy as economy

def database():
    db=sqlite3.connect(":memory:")
    db.row_factory=sqlite3.Row
    db.executescript("""
    CREATE TABLE ashfall_economy_clock(haven_id INTEGER PRIMARY KEY,last_tick REAL,
      food_fraction REAL DEFAULT 0,wood_fraction REAL DEFAULT 0,
      metal_fraction REAL DEFAULT 0,gas_fraction REAL DEFAULT 0);
    CREATE TABLE ashfall_building_levels(haven_id INTEGER,building_key TEXT,level INTEGER,
      PRIMARY KEY(haven_id,building_key));
    CREATE TABLE ashfall_resource_balances(haven_id INTEGER PRIMARY KEY,
      food INTEGER DEFAULT 0,wood INTEGER DEFAULT 0,metal INTEGER DEFAULT 0,gas INTEGER DEFAULT 0);
    CREATE TABLE ashfall_construction_queue(haven_id INTEGER PRIMARY KEY,
      building_key TEXT,target_level INTEGER,finishes_at REAL);
    CREATE TABLE ashfall_economic_doctrine(haven_id INTEGER PRIMARY KEY,focus TEXT,changed_at REAL);
    CREATE TABLE ashfall_doctrine_mastery(haven_id INTEGER,focus TEXT,active_seconds REAL,
      PRIMARY KEY(haven_id,focus));
    CREATE TABLE ashfall_havens(id INTEGER PRIMARY KEY,command_center_level INTEGER);
    """)
    db.execute("INSERT INTO ashfall_havens VALUES(1,1)")
    db.execute("INSERT INTO ashfall_resource_balances(haven_id) VALUES(1)")
    db.execute("INSERT INTO ashfall_economy_clock(haven_id,last_tick) VALUES(1,0)")
    db.execute("INSERT INTO ashfall_economic_doctrine VALUES(1,'agriculture',0)")
    for key in economy.BUILDINGS:
        db.execute("INSERT INTO ashfall_building_levels VALUES(1,?,?)",
                   (key,1 if key in ("hq","farm") else 0))
    return db

def accrue(db,now):
    with patch.object(economy,"prepare",lambda *_:None),patch.object(
        economy,"production_bonus",lambda *_:0):
        economy.accrue(db,1,now)

def test_mastery_boundary_and_idempotency():
    db=database()
    accrue(db,86400)
    first=db.execute("SELECT food FROM ashfall_resource_balances").fetchone()[0]
    assert first==int(120*1.08*24),first
    rank=economy.mastery_status(db,1)["agriculture"]
    assert rank["rank"]==1,rank
    accrue(db,172800)
    total=db.execute("SELECT food FROM ashfall_resource_balances").fetchone()[0]
    assert total-first==int(120*1.09*24),total-first
    accrue(db,172800)
    assert db.execute("SELECT food FROM ashfall_resource_balances").fetchone()[0]==total
    db.close()

def test_construction_completion_starts_mastery_only_after_activation():
    db=database()
    db.execute("UPDATE ashfall_building_levels SET level=0 WHERE building_key='farm'")
    db.execute("INSERT INTO ashfall_construction_queue VALUES(1,'farm',1,3600)")
    accrue(db,7200)
    status=economy.mastery_status(db,1)["agriculture"]
    assert status["active_seconds"]==3600,status
    food=db.execute("SELECT food FROM ashfall_resource_balances").fetchone()[0]
    assert food==129,food  # one hour at 120/h with 8% doctrine bonus
    db.close()

def test_switch_preserves_mastery_without_retroactive_bonus():
    db=database()
    accrue(db,86400)
    before=db.execute("SELECT food FROM ashfall_resource_balances").fetchone()[0]
    db.execute("UPDATE ashfall_economic_doctrine SET focus='forestry',changed_at=86400 WHERE haven_id=1")
    accrue(db,90000)
    after=db.execute("SELECT food FROM ashfall_resource_balances").fetchone()[0]
    assert after-before==120,after-before  # farm now has no agriculture doctrine bonus
    assert economy.mastery_status(db,1)["agriculture"]["rank"]==1
    assert economy.mastery_status(db,1)["forestry"]["active_seconds"]==0
    db.close()

if __name__=="__main__":
    test_mastery_boundary_and_idempotency()
    test_construction_completion_starts_mastery_only_after_activation()
    test_switch_preserves_mastery_without_retroactive_bonus()
    print("ASHFALL SQLite doctrine integration checks passed")
