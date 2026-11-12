"""NEXORA 83 — complete player strategic pipeline against real ASHFALL schema.

No mocked production rates, no simulated awards, no client-owned Haven data.
Runs every NEXORA 69–79 projection on a fresh SQLite game database.
"""
import sqlite3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ashfall_economy import initialize as initialize_economy, prepare, accrue, snapshot, BUILDINGS
from app.nexora_universal_chronicle import universal_chronicle
from app.nexora_achievement_discovery import achievement_discovery
from app.nexora_collection_mastery import collection_mastery
from app.nexora_achievement_pursuits import achievement_pursuits
from app.nexora_settlement_intelligence import settlement_milestone_intelligence
from app.nexora_development_roadmap import development_roadmap
from app.nexora_resource_forecast import resource_forecast
from app.nexora_economic_readiness import economic_readiness
from app.nexora_strategic_command import strategic_command_overview


def database():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript("""
        CREATE TABLE ashfall_havens(
            id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, state_id INTEGER NOT NULL DEFAULT 1,\n            command_center_level INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE player_achievements(
            user_id INTEGER NOT NULL, achievement_key TEXT NOT NULL,
            unlocked_at TEXT NOT NULL, PRIMARY KEY(user_id,achievement_key)
        );
        INSERT INTO ashfall_havens(id,user_id) VALUES(1,7),(2,8);
        INSERT INTO player_achievements VALUES(7,'first-arrival','2026-01-01T00:00:00+00:00');
        INSERT INTO player_achievements VALUES(8,'first-arrival','2026-01-01T00:00:00+00:00');
    """)
    initialize_economy(db)
    db.commit()
    return db


def project(db, user_id):
    chronicle = universal_chronicle(db, user_id)
    discovery = achievement_discovery(chronicle)
    mastery = collection_mastery(discovery)
    pursuits = achievement_pursuits(discovery)
    intel = settlement_milestone_intelligence(db, user_id)
    roadmap = development_roadmap(intel)
    forecast = resource_forecast(db, user_id, roadmap)
    readiness = economic_readiness(db, user_id, forecast)
    overview = strategic_command_overview(
        discovery, mastery, pursuits, intel, roadmap, forecast, readiness
    )
    return {
        "chronicle": chronicle, "discovery": discovery, "mastery": mastery,
        "pursuits": pursuits, "intelligence": intel, "roadmap": roadmap,
        "forecast": forecast, "readiness": readiness, "overview": overview,
    }


def test_fresh_haven_is_read_only_and_scoped():
    db = database()
    before = db.total_changes
    player = project(db, 7)
    assert db.total_changes == before, "Profile projection must never mutate game state"
    assert player["intelligence"]["haven_count"] == 1
    assert [item["haven_id"] for item in player["roadmap"]["havens"]] == [1]
    assert [item["haven_id"] for item in player["forecast"]["havens"]] == [1]
    assert [item["haven_id"] for item in player["readiness"]["havens"]] == [1]
    assert player["overview"]["settlement"]["haven_id"] == 1
    assert player["overview"]["collection"]["total"] >= 1
    assert player["overview"]["upgrade"]["name"] in (
        definition["name"] for definition in BUILDINGS.values()
    )
    assert all(not quote["affordable"] for quote in player["forecast"]["havens"][0]["quotes"])
    assert all("initialize Haven economy" in " ".join(quote["blocked"])
               for quote in player["forecast"]["havens"][0]["quotes"])
    assert project(db, 8)["overview"]["settlement"]["haven_id"] == 2
    assert db.total_changes == before


def test_early_progress_and_balances():
    db = database()
    for key in BUILDINGS:
        db.execute("INSERT INTO ashfall_building_levels VALUES(?,?,?)", (
            1, key, 1 if key == "hq" else 0
        ))
    db.execute("INSERT INTO ashfall_resource_balances(haven_id,food,wood,metal,gas) VALUES(1,900,900,900,900)")
    db.commit()
    before = db.total_changes
    report = project(db, 7)
    quotes = report["forecast"]["havens"][0]["quotes"]
    assert quotes
    assert any(quote["affordable"] for quote in quotes)
    assert db.total_changes == before


def test_completed_construction_and_milestone_refresh():
    db = database()
    start = 100000.0
    prepare(db, 1, start)
    # Five facilities already qualify; a real queued HQ upgrade is the final
    # level-five requirement. Accrual completes the queue, snapshot awards.
    for key in BUILDINGS:
        db.execute(
            "UPDATE ashfall_building_levels SET level=? WHERE haven_id=1 AND building_key=?",
            (4 if key == "hq" else 5, key),
        )
    db.execute(
        "INSERT INTO ashfall_construction_queue(haven_id,building_key,target_level,finishes_at) "
        "VALUES(1,'hq',5,?)", (start + 10,),
    )
    db.commit()
    before = project(db, 7)
    assert before["intelligence"]["havens"][0]["target_level"] == 5
    assert before["forecast"]["havens"][0]["queue_occupied"]
    assert before["discovery"]["earned"] == 1
    assert before["overview"]["settlement"]["remaining_levels"] == 1
    # Profile reads never settle construction or award milestones.
    assert db.execute("SELECT target_level FROM ashfall_construction_queue WHERE haven_id=1").fetchone()
    accrue(db, 1, start + 11)
    assert db.execute("SELECT level FROM ashfall_building_levels WHERE haven_id=1 AND building_key='hq'").fetchone()["level"] == 5
    assert not db.execute("SELECT 1 FROM ashfall_construction_queue WHERE haven_id=1").fetchone()
    # ASHFALL's authoritative snapshot evaluates and records the award.
    state = snapshot(db, 1, start + 11)
    assert any(tier["level"] == 5 and tier["earned"] for tier in state["settlement_achievements"]["tiers"])
    db.commit()
    changes = db.total_changes
    after = project(db, 7)
    assert db.total_changes == changes
    assert after["discovery"]["earned"] == before["discovery"]["earned"] + 1
    assert after["intelligence"]["havens"][0]["target_level"] == 15
    assert after["overview"]["settlement"]["remaining_levels"] > 1
    assert after["overview"]["collection"]["earned"] == after["discovery"]["earned"]
    assert after["chronicle"]["ashfall_prestige"] >= 100
    assert project(db, 8)["chronicle"]["ashfall_prestige"] == 0
    # Repeated authoritative snapshots cannot grant the same chapter twice.
    snapshot(db, 1, start + 11)
    db.commit()
    replay = project(db, 7)
    assert replay["chronicle"]["ashfall_prestige"] == after["chronicle"]["ashfall_prestige"]
    assert replay["discovery"]["earned"] == after["discovery"]["earned"]


def test_multiple_havens_collect_tier_once():
    db = database()
    db.execute("INSERT INTO ashfall_havens(id,user_id,state_id) VALUES(3,7,2)")
    for haven in (1, 3):
        prepare(db, haven, 100000.0)
        for key in BUILDINGS:
            db.execute(
                "UPDATE ashfall_building_levels SET level=5 WHERE haven_id=? AND building_key=?",
                (haven, key),
            )
        snapshot(db, haven, 100000.0)
    db.commit()
    before = db.total_changes
    report = project(db, 7)
    assert report["chronicle"]["ashfall_prestige"] == 200
    assert report["chronicle"]["world_earned"] == 2
    # Discovery collects each world-level goal only once per player.
    assert report["discovery"]["earned"] == 2
    assert report["intelligence"]["haven_count"] == 2
    assert all(haven["target_level"] == 15 for haven in report["intelligence"]["havens"])
    assert db.total_changes == before
    assert project(db, 8)["chronicle"]["ashfall_prestige"] == 0


def test_no_haven_player():
    db = database()
    before = db.total_changes
    report = project(db, 42)
    assert report["overview"]["settlement"] is None
    assert report["overview"]["upgrade"] is None
    assert report["overview"]["havens_count"] == 0
    assert db.total_changes == before


if __name__ == "__main__":
    test_fresh_haven_is_read_only_and_scoped()
    test_early_progress_and_balances()
    test_no_haven_player()\n    test_completed_construction_and_milestone_refresh()\n    test_multiple_havens_collect_tier_once()
    print("NEXORA 83 complete profile integration checks passed")
