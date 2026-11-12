"""NEXORA 78 — economic readiness arithmetic, blockers and ownership."""
import sqlite3
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app.nexora_economic_readiness as readiness


def database():
    db=sqlite3.connect(":memory:")
    db.row_factory=sqlite3.Row
    db.executescript("""
    CREATE TABLE ashfall_havens(id INTEGER PRIMARY KEY,user_id INTEGER);
    CREATE TABLE ashfall_building_levels(haven_id INTEGER,building_key TEXT,level INTEGER);
    INSERT INTO ashfall_havens VALUES(1,7);
    INSERT INTO ashfall_havens VALUES(2,8);
    """)
    return db


def forecast(quote, haven=1):
    return {"havens":[{"haven_id":haven,"queue_occupied":False,"quotes":[quote]}]}


def quote(**changes):
    result={"key":"farm","name":"Farm","shortages":{"wood":100,"metal":50},
            "rare_shortages":{},"blocked":[]}
    result.update(changes)
    return result


def test_parallel_resource_estimate_and_read_only():
    db=database()
    original=readiness.production_breakdown
    readiness.production_breakdown=lambda *args,**kwargs:{
        "wood":{"per_hour":50,"facility":"lumber"},
        "metal":{"per_hour":10,"facility":"salvage"},
    }
    try:
        before=db.total_changes
        result=readiness.economic_readiness(db,7,forecast(quote()))
        item=result["havens"][0]["quotes"][0]
        assert item["status"]=="production_estimate"
        assert item["estimated_hours"]==5
        assert item["limiting_resource"]=="metal"
        assert db.total_changes==before
    finally:
        readiness.production_breakdown=original


def test_missing_production_and_rare_materials():
    db=database()
    original=readiness.production_breakdown
    readiness.production_breakdown=lambda *args,**kwargs:{}
    try:
        item=readiness.economic_readiness(db,7,forecast(quote()))["havens"][0]["quotes"][0]
        assert item["status"]=="production_unavailable"
        assert item["estimated_hours"] is None
        item=readiness.economic_readiness(db,7,forecast(
            quote(shortages={},rare_shortages={"crystal_shards":8})))["havens"][0]["quotes"][0]
        assert item["status"]=="rare_material_shortage"
    finally:
        readiness.production_breakdown=original


def test_foreign_haven_is_rejected():
    try:
        readiness.economic_readiness(database(),7,forecast(quote(),2))
    except ValueError:
        pass
    else:
        raise AssertionError("Foreign Haven accepted")


if __name__=="__main__":
    test_parallel_resource_estimate_and_read_only()
    test_missing_production_and_rare_materials()
    test_foreign_haven_is_rejected()
    print("NEXORA 78 economic readiness checks passed")
