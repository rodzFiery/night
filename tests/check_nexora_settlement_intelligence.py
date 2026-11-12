"""NEXORA 75 — isolated account-scoped ASHFALL development intelligence tests."""
import sqlite3
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.nexora_settlement_intelligence import settlement_milestone_intelligence


def database():
    db=sqlite3.connect(":memory:")
    db.row_factory=sqlite3.Row
    db.execute("CREATE TABLE ashfall_havens(id INTEGER PRIMARY KEY,user_id INTEGER NOT NULL)")
    db.execute("CREATE TABLE ashfall_building_levels(haven_id INTEGER,building_key TEXT,level INTEGER)")
    db.execute("CREATE TABLE ashfall_settlement_achievements(haven_id INTEGER,milestone_level INTEGER)")
    db.executemany("INSERT INTO ashfall_havens VALUES(?,?)",[(1,10),(2,10),(3,20)])
    for haven,level in ((1,4),(2,3),(3,50)):
        for key in ("hq","farm","lumber","salvage","fuel","barracks"):
            db.execute("INSERT INTO ashfall_building_levels VALUES(?,?,?)",(haven,key,level))
    db.execute("UPDATE ashfall_building_levels SET level=5 WHERE haven_id=1 AND building_key='hq'")
    db.execute("INSERT INTO ashfall_settlement_achievements VALUES(3,5)")
    return db


def test_owned_havens_only_and_bottlenecks():
    db=database()
    before=db.total_changes
    report=settlement_milestone_intelligence(db,10)
    assert report["haven_count"]==2
    assert [h["haven_id"] for h in report["havens"]]==[1,2]
    assert report["recommended_haven"]==1
    assert report["havens"][0]["reached"]==1
    assert report["havens"][0]["remaining_levels"]==5
    assert report["havens"][1]["remaining_levels"]==12
    assert db.total_changes==before
    assert settlement_milestone_intelligence(db,999)["havens"]==[]


def test_earned_chapter_moves_target_forward():
    db=database()
    db.execute("INSERT INTO ashfall_settlement_achievements VALUES(1,5)")
    report=settlement_milestone_intelligence(db,10)
    first=next(h for h in report["havens"] if h["haven_id"]==1)
    assert first["target_level"]==15
    assert first["remaining_levels"]==65


def test_missing_facilities_are_not_credited():
    db=database()
    db.execute("DELETE FROM ashfall_building_levels WHERE haven_id=1 AND building_key='farm'")
    report=settlement_milestone_intelligence(db,10)
    first=next(h for h in report["havens"] if h["haven_id"]==1)
    assert next(f for f in first["facilities"] if f["key"]=="farm")["level"]==0
    assert first["remaining_levels"]==9


if __name__=="__main__":
    test_owned_havens_only_and_bottlenecks()
    test_earned_chapter_moves_target_forward()
    test_missing_facilities_are_not_credited()
    print("NEXORA 75 settlement intelligence checks passed")
