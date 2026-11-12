"""NEXORA 69 — deterministic universal Chronicle ownership and ordering checks."""
import sqlite3
from app import ashfall_settlement_achievements as achievements
from app.nexora_universal_chronicle import universal_chronicle


def database():
    db=sqlite3.connect(":memory:")
    db.row_factory=sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("CREATE TABLE users(id INTEGER PRIMARY KEY)")
    db.execute("CREATE TABLE ashfall_havens(id INTEGER PRIMARY KEY,user_id INTEGER NOT NULL REFERENCES users(id))")
    db.execute("""CREATE TABLE player_achievements(
        user_id INTEGER NOT NULL REFERENCES users(id),
        achievement_key TEXT NOT NULL,
        unlocked_at TEXT NOT NULL,
        UNIQUE(user_id,achievement_key))""")
    db.executemany("INSERT INTO users(id) VALUES(?)",[(1,),(2,)])
    db.executemany("INSERT INTO ashfall_havens(id,user_id) VALUES(?,?)",[(10,1),(20,2)])
    achievements.initialize(db)
    return db


def test_cross_world_aggregation_and_ownership():
    db=database()
    db.execute("INSERT INTO player_achievements VALUES(1,'first-arrival','2026-01-01T00:00:00+00:00')")
    db.execute("INSERT INTO player_achievements VALUES(2,'first-arrival','2026-01-02T00:00:00+00:00')")
    achievements.evaluate(db,10,{key:5 for key in achievements.FACILITIES},1767312000)
    achievements.evaluate(db,20,{key:15 for key in achievements.FACILITIES},1767398400)
    first=universal_chronicle(db,1)
    second=universal_chronicle(db,2)
    assert first["total_earned"]==2
    assert first["platform_earned"]==1 and first["world_earned"]==1
    assert first["ashfall_prestige"]==100
    assert second["total_earned"]==3 and second["ashfall_prestige"]==400
    assert all(":20:" not in event["id"] for event in first["events"])
    assert first["events"]==sorted(first["events"],key=lambda item:(item["earned_at"],item["world"],item["id"]))
    assert universal_chronicle(db,999)["events"]==[]
    db.close()


def test_projection_is_read_only_and_stable():
    db=database()
    db.execute("INSERT INTO player_achievements VALUES(1,'first-arrival','2026-01-01T00:00:00Z')")
    before=db.total_changes
    first=universal_chronicle(db,1)
    second=universal_chronicle(db,1)
    assert first==second
    assert db.total_changes==before
    assert first["events"][0]["earned_at"]=="2026-01-01T00:00:00+00:00"
    db.close()


if __name__=="__main__":
    test_cross_world_aggregation_and_ownership()
    test_projection_is_read_only_and_stable()
    print("NEXORA 69 universal Chronicle checks passed")
