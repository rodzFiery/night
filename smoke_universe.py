"""NEXORA Universe 2.0 smoke checks. Run from project root with venv Python.

This verifies import, route registration, Jinja syntax, and schema without
submitting claims, sending messages, or changing passwords.
"""
import os
import tempfile
from pathlib import Path

# Use an isolated disposable database, never the player's existing save.
with tempfile.TemporaryDirectory(prefix="nexora-smoke-") as directory:
    os.environ["NEXORA_DATA_DIR"] = directory
    os.environ["NEXORA_DB_PATH"] = str(Path(directory) / "smoke.db")
    os.environ["NEXORA_SECRET_KEY"] = "test-only-not-for-production"
    from app.main import app, templates, database

    expected = {
        "/universe", "/universe/mission/{mission_key}",
        "/universe/identity", "/universe/message", "/universe/password",
        "/universe/notifications/read", "/universe/notifications/preferences",
        "/universe/block",
    }
    paths = {route.path for route in app.routes}
    missing = expected - paths
    assert not missing, f"Missing routes: {sorted(missing)}"
    templates.env.get_template("universe.html")
    templates.env.get_template("dashboard.html")
    with database() as db:
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    required = {
        "users", "player_progress", "progression_events",
        "universe_identity", "universe_mission_claims", "universe_messages",
        "universe_notification_preferences", "universe_blocked_players",
    }
    assert required <= tables, f"Missing tables: {sorted(required - tables)}"
    print("PASS: Universe 2.0 routes, templates, and database schema.")
    print("No real player data was accessed or modified.")
