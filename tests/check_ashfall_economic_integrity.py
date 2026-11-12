"""ASHFALL 60: deterministic economic integrity checks against isolated SQLite.

The server remains authoritative; no production accounts or resources are touched.
Run: PYTHONPATH=. python tests/check_ashfall_economic_integrity.py
"""
from unittest.mock import patch
from pathlib import Path
import sys
from app import ashfall_economy as economy
sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_ashfall_doctrine_db import database


def test_snapshot_is_idempotent_and_rates_are_authoritative():
    db = database()
    db.execute("""CREATE TABLE ashfall_crystal_balances(\n        haven_id INTEGER PRIMARY KEY, crystal_shards INTEGER DEFAULT 0,\n        ancient_cores INTEGER DEFAULT 0, prismatic_essence INTEGER DEFAULT 0,\n        last_salvage_at REAL DEFAULT 0)""")
    with patch.object(economy, "prepare", lambda *_: None), patch.object(
        economy, "production_bonus", lambda *_: 0
    ):
        first = economy.snapshot(db, 1, 3600)
        second = economy.snapshot(db, 1, 3600)
    assert first["resources"] == second["resources"], "Duplicate snapshot minted resources"
    assert first["resources"]["food"] == 129, first["resources"]
    assert first["production_rates"]["food"]["per_hour"] == round(
        economy.production_per_hour(120, 1, doctrine_bonus=.08), 2
    )
    assert first["production_rates"]["wood"]["per_hour"] == 0
    assert first["production_rates"]["metal"]["per_hour"] == 0
    assert first["production_rates"]["gas"]["per_hour"] == 0
    db.close()


def test_production_breakdown_reflects_research_alliance_and_mastery():
    db = database()
    db.execute("CREATE TABLE ashfall_technology(haven_id INTEGER,tech_key TEXT,level INTEGER)")
    db.execute("INSERT INTO ashfall_technology VALUES(1,'agriculture',2)")
    db.execute("INSERT INTO ashfall_doctrine_mastery VALUES(1,'agriculture',86400)")
    levels = {row["building_key"]: row["level"] for row in db.execute(
        "SELECT building_key,level FROM ashfall_building_levels WHERE haven_id=1"
    )}
    with patch.object(
        economy, "production_bonus", lambda db, haven, resource: .10 if resource == "food" else 0
    ):
        report = economy.production_breakdown(db, 1, levels, 86400)
    food = report["food"]
    assert food["per_hour"] == round(
        economy.production_per_hour(120, 1, 2, .10, .09), 2
    ), food
    assert food["research_level"] == 2
    assert food["alliance_bonus"] == .10
    assert food["doctrine_bonus"] == .09
    db.close()


def test_offline_clock_never_rewinds():
    db = database()
    with patch.object(economy, "prepare", lambda *_: None), patch.object(
        economy, "production_bonus", lambda *_: 0
    ):
        economy.accrue(db, 1, 7200)
        before = db.execute(
            "SELECT food FROM ashfall_resource_balances WHERE haven_id=1"
        ).fetchone()[0]
        economy.accrue(db, 1, 3600)
        after = db.execute(
            "SELECT food FROM ashfall_resource_balances WHERE haven_id=1"
        ).fetchone()[0]
    assert before == after
    assert db.execute(
        "SELECT last_tick FROM ashfall_economy_clock WHERE haven_id=1"
    ).fetchone()[0] == 7200
    db.close()


if __name__ == "__main__":
    test_snapshot_is_idempotent_and_rates_are_authoritative()
    test_production_breakdown_reflects_research_alliance_and_mastery()
    test_offline_clock_never_rewinds()
    print("ASHFALL 60 economic integrity checks passed")
