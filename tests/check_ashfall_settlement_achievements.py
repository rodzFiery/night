"""ASHFALL 65 — isolated, deterministic settlement achievement checks."""
import sqlite3
from app import ashfall_settlement_achievements as achievements


def database():
    db=sqlite3.connect(":memory:")
    db.row_factory=sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE TABLE ashfall_havens(id INTEGER PRIMARY KEY)")
    db.executemany("INSERT INTO ashfall_havens(id) VALUES(?)",[(1,),(2,)])
    achievements.initialize(db)
    return db


def levels(value):
    return {key:value for key in achievements.FACILITIES}


def test_permanent_awards_are_idempotent():
    db=database()
    first=achievements.evaluate(db,1,levels(15),1000)
    assert first["earned_count"]==2,first
    second=achievements.evaluate(db,1,levels(15),2000)
    assert second["earned_count"]==2
    rows=db.execute("SELECT milestone_level,earned_at FROM ashfall_settlement_achievements WHERE haven_id=1 ORDER BY milestone_level").fetchall()
    assert [(row["milestone_level"],row["earned_at"]) for row in rows]==[(5,1000),(15,1000)]
    db.close()


def test_awards_survive_lower_levels_and_remain_isolated():
    db=database()
    achievements.evaluate(db,1,levels(50),100)
    after=achievements.evaluate(db,1,levels(0),200)
    assert after["earned_count"]==4
    assert all(tier["earned"] for tier in after["tiers"])
    assert achievements.status(db,2,levels(0))["earned_count"]==0
    db.close()


def test_partial_settlement_cannot_claim_threshold():
    db=database()
    current=levels(5)
    current["fuel"]=4
    result=achievements.evaluate(db,1,current,500)
    assert result["earned_count"]==0
    assert result["tiers"][0]["reached"]==5
    db.close()


def test_incomplete_levels_are_rejected():
    db=database()
    try:
        achievements.evaluate(db,1,{"hq":50},100)
    except ValueError:
        pass
    else:
        raise AssertionError("Incomplete facility levels must not award achievements")
    db.close()


def test_foreign_key_cleanup():
    db=database()
    achievements.evaluate(db,1,levels(5),100)
    db.execute("DELETE FROM ashfall_havens WHERE id=1")
    assert db.execute("SELECT COUNT(*) FROM ashfall_settlement_achievements").fetchone()[0]==0
    db.close()


if __name__=="__main__":
    test_permanent_awards_are_idempotent()
    test_awards_survive_lower_levels_and_remain_isolated()
    test_partial_settlement_cannot_claim_threshold()
    test_incomplete_levels_are_rejected()
    test_foreign_key_cleanup()
    print("ASHFALL 65 settlement achievement checks passed")
