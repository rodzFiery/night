"""NEXORA 83 — complete player strategic pipeline against real ASHFALL schema.

No mocked production rates, no simulated awards, no client-owned Haven data.
Runs every NEXORA 69–79 projection on a fresh SQLite game database.
"""
import sqlite3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ashfall_economy import initialize as initialize_economy, BUILDINGS
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
            id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, state_id INTEGER NOT NULL DEFAULT 1
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
    test_no_haven_player()
    print("NEXORA 83 complete profile integration checks passed")
