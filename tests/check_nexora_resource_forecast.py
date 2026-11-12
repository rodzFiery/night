"""NEXORA 77 — construction pricing, shortages and owner isolation."""
import sqlite3
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.nexora_resource_forecast import resource_forecast
from app.ashfall_economy import BUILDINGS
from app.ashfall_crystal_age import conventional_cost, construction_seconds


def fixture():
    db=sqlite3.connect(":memory:")
    db.row_factory=sqlite3.Row
    db.executescript("""
    CREATE TABLE ashfall_havens(id INTEGER PRIMARY KEY,user_id INTEGER);
    CREATE TABLE ashfall_building_levels(haven_id INTEGER,building_key TEXT,level INTEGER);
    CREATE TABLE ashfall_resource_balances(haven_id INTEGER,food INTEGER,wood INTEGER,metal INTEGER,gas INTEGER);
    CREATE TABLE ashfall_crystal_balances(haven_id INTEGER,crystal_shards INTEGER,ancient_cores INTEGER,prismatic_essence INTEGER);
    CREATE TABLE ashfall_construction_queue(haven_id INTEGER,building_key TEXT);
    CREATE TABLE ashfall_crystal_frontier_research(haven_id INTEGER,tech_key TEXT,level INTEGER);
    """)
    db.executemany("INSERT INTO ashfall_havens VALUES(?,?)",[(1,7),(2,8)])
    for hid in (1,2):
        for key in BUILDINGS:
            db.execute("INSERT INTO ashfall_building_levels VALUES(?,?,?)",(hid,key,5 if key=="hq" else 1))
        db.execute("INSERT INTO ashfall_resource_balances VALUES(?,?,?,?,?)",(hid,0,0,0,0))
        db.execute("INSERT INTO ashfall_crystal_balances VALUES(?,?,?,?)",(hid,0,0,0))
    return db


def roadmap(haven_id=1):
    return {"havens":[{"haven_id":haven_id,"complete":False,
        "steps":[{"key":"farm","current":1,"priority":1}]}]}


def test_quotes_match_economy_and_are_read_only():
    db=fixture()
    before=db.total_changes
    report=resource_forecast(db,7,roadmap())
    quote=report["havens"][0]["quotes"][0]
    assert quote["cost"]==conventional_cost(BUILDINGS["farm"]["cost"],1,0)
    assert quote["seconds"]==construction_seconds(BUILDINGS["farm"]["seconds"],1,0)
    assert quote["shortages"]==quote["cost"]
    assert not quote["affordable"]
    assert db.total_changes==before


def test_prerequisites_and_queue_block():
    db=fixture()
    db.execute("INSERT INTO ashfall_construction_queue VALUES(?,?)",(1,"farm"))
    report=resource_forecast(db,7,roadmap())
    assert "Construction slot occupied" in report["havens"][0]["quotes"][0]["blocked"]


def test_foreign_and_stale_roadmap_rejected():
    db=fixture()
    for user,plan in ((7,roadmap(2)),(7,{"havens":[{"haven_id":1,"complete":False,
        "steps":[{"key":"farm","current":99,"priority":1}]}]})):
        try:
            resource_forecast(db,user,plan)
        except ValueError:
            pass
        else:
            raise AssertionError("Unsafe roadmap accepted")


if __name__=="__main__":
    test_quotes_match_economy_and_are_read_only()
    test_prerequisites_and_queue_block()
    test_foreign_and_stale_roadmap_rejected()
    print("NEXORA 77 resource forecast checks passed")
