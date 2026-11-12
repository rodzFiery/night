"""ASHFALL 47 — SQLite integration checks for offline doctrine mastery.

Runs against the actual accrue/snapshot engine with isolated in-memory tables.
No production accounts, network services, or migrations are modified.
"""
import sqlite3
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
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

def test_no_mastery_without_operational_production():
    db=database()
    db.execute("UPDATE ashfall_building_levels SET level=0 WHERE building_key='farm'")
    accrue(db,86400)
    mastery=economy.mastery_status(db,1)["agriculture"]
    assert mastery["rank"]==0,mastery
    assert mastery["active_seconds"]==0,mastery
    assert db.execute("SELECT food FROM ashfall_resource_balances").fetchone()[0]==0
    db.close()

def test_mastery_isolated_by_haven_and_focus():
    db=database()
    db.execute("INSERT INTO ashfall_havens VALUES(2,1)")
    db.execute("INSERT INTO ashfall_resource_balances(haven_id) VALUES(2)")
    db.execute("INSERT INTO ashfall_economy_clock(haven_id,last_tick) VALUES(2,0)")
    db.execute("INSERT INTO ashfall_economic_doctrine VALUES(2,'energy',0)")
    for key in economy.BUILDINGS:
        db.execute("INSERT INTO ashfall_building_levels VALUES(2,?,?)",
                   (key,1 if key in ("hq","fuel") else 0))
    with patch.object(economy,"prepare",lambda *_:None),patch.object(
        economy,"production_bonus",lambda *_:0):
        economy.accrue(db,1,86400)
        economy.accrue(db,2,86400)
    one=economy.mastery_status(db,1)
    two=economy.mastery_status(db,2)
    assert one["agriculture"]["rank"]==1 and one["energy"]["rank"]==0
    assert two["energy"]["rank"]==1 and two["agriculture"]["rank"]==0
    assert db.execute("SELECT gas FROM ashfall_resource_balances WHERE haven_id=1").fetchone()[0]==0
    assert db.execute("SELECT food FROM ashfall_resource_balances WHERE haven_id=2").fetchone()[0]==0
    db.close()

def test_research_and_alliance_bonuses_stack_with_mastery():
    db=database()
    db.execute("CREATE TABLE ashfall_technology(haven_id INTEGER,tech_key TEXT,level INTEGER)")
    db.execute("CREATE TABLE ashfall_research_queue(haven_id INTEGER,tech_key TEXT,target_level INTEGER,finishes_at REAL)")
    db.execute("INSERT INTO ashfall_technology VALUES(1,'agriculture',2)")
    # Start with one full mastery rank; the focused production multiplier
    # must include research, alliance and mastery, not replace any of them.
    db.execute("INSERT INTO ashfall_doctrine_mastery VALUES(1,'agriculture',86400)")
    with patch.object(economy,"prepare",lambda *_:None),patch.object(
        economy,"production_bonus",lambda db,hid,res:.10 if res=="food" else 0):
        economy.accrue(db,1,3600)
    actual=db.execute("SELECT food FROM ashfall_resource_balances").fetchone()[0]
    expected=int(economy.production_per_hour(
        120,1,research_level=2,alliance_bonus=.10,doctrine_bonus=.09))
    assert actual==expected,(actual,expected)
    db.close()

def test_clock_rewind_cannot_duplicate_production():
    db=database()
    accrue(db,3600)
    first=db.execute("SELECT food FROM ashfall_resource_balances").fetchone()[0]
    accrue(db,3500)
    assert db.execute("SELECT food FROM ashfall_resource_balances").fetchone()[0]==first
    assert db.execute("SELECT last_tick FROM ashfall_economy_clock").fetchone()[0]==3600
    accrue(db,7200)
    expected=int(economy.production_per_hour(120,1,doctrine_bonus=.08)*2)
    actual=db.execute("SELECT food FROM ashfall_resource_balances").fetchone()[0]
    assert actual==expected,(actual,expected)
    db.close()

def test_overdue_construction_queue_recovers():
    db=database()
    db.execute("UPDATE ashfall_economy_clock SET last_tick=7200")
    db.execute("UPDATE ashfall_building_levels SET level=0 WHERE building_key='farm'")
    db.execute("INSERT INTO ashfall_construction_queue VALUES(1,'farm',1,3600)")
    accrue(db,10800)
    assert db.execute("SELECT COUNT(*) FROM ashfall_construction_queue").fetchone()[0]==0
    assert db.execute("SELECT level FROM ashfall_building_levels WHERE building_key='farm'").fetchone()[0]==1
    assert economy.mastery_status(db,1)["agriculture"]["active_seconds"]==3600
    db.close()

def test_parallel_snapshot_transactions_do_not_double_credit():
    # The real API uses BEGIN IMMEDIATE before snapshot(); reproduce that
    # transaction boundary using two independent SQLite connections.
    source=database()
    with tempfile.TemporaryDirectory() as directory:
        path=Path(directory)/"economy.sqlite3"
        target=sqlite3.connect(str(path))
        source.backup(target)
        target.close()
        source.close()

        def poll():
            connection=sqlite3.connect(str(path),timeout=10)
            connection.row_factory=sqlite3.Row
            try:
                connection.execute("BEGIN IMMEDIATE")
                with patch.object(economy,"prepare",lambda *_:None),patch.object(
                    economy,"production_bonus",lambda *_:0):
                    economy.accrue(connection,1,3600)
                connection.commit()
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(lambda _:poll(),range(2)))
        check=sqlite3.connect(str(path))
        amount=check.execute("SELECT food FROM ashfall_resource_balances WHERE haven_id=1").fetchone()[0]
        expected=int(economy.production_per_hour(120,1,doctrine_bonus=.08))
        assert amount==expected,(amount,expected)
        check.close()

if __name__=="__main__":
    test_mastery_boundary_and_idempotency()
    test_construction_completion_starts_mastery_only_after_activation()
    test_switch_preserves_mastery_without_retroactive_bonus()
    test_no_mastery_without_operational_production()
    test_mastery_isolated_by_haven_and_focus()
    test_research_and_alliance_bonuses_stack_with_mastery()
    test_clock_rewind_cannot_duplicate_production()
    test_overdue_construction_queue_recovers()
    test_parallel_snapshot_transactions_do_not_double_credit()
    print("ASHFALL SQLite doctrine integration checks passed")
