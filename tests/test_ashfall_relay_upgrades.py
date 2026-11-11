"""ASHFALL 5.0 industrial relay level and timer tests."""
import sqlite3
import unittest
from app.ashfall_relay_upgrades import effective_level,upgrade_status,UPGRADE_COSTS,UPGRADE_SECONDS
from app.ashfall_theater_relays import scouting_relay_bonus

class IndustrialRelayTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(":memory:")
        self.db.row_factory=sqlite3.Row
        self.db.executescript("""
            CREATE TABLE ashfall_theater_relays(
                haven_id INTEGER,state_id INTEGER,theater_x INTEGER,theater_y INTEGER,
                started_at REAL,finishes_at REAL);
            CREATE TABLE ashfall_relay_upgrades(
                haven_id INTEGER,state_id INTEGER,theater_x INTEGER,theater_y INTEGER,
                level INTEGER,finishes_at REAL);
            INSERT INTO ashfall_theater_relays VALUES(1,1,1,1,100,200);
            INSERT INTO ashfall_relay_upgrades VALUES(1,1,1,1,1,400);
        """)

    def tearDown(self):
        self.db.close()

    def test_upgrade_pending_does_not_unlock_level(self):
        row=self.db.execute("SELECT level,finishes_at FROM ashfall_relay_upgrades").fetchone()
        self.assertEqual(effective_level(row,399),1)

    def test_upgrade_completes_at_server_time(self):
        row=self.db.execute("SELECT level,finishes_at FROM ashfall_relay_upgrades").fetchone()
        self.assertEqual(effective_level(row,400),2)

    def test_pending_upgrade_no_early_bonus(self):
        self.assertEqual(scouting_relay_bonus(self.db,1,1,4,4,399),10)

    def test_completed_upgrade_improves_real_bonus(self):
        self.assertEqual(scouting_relay_bonus(self.db,1,1,4,4,400),13)

    def test_upgrade_isolation(self):
        self.assertEqual(scouting_relay_bonus(self.db,2,1,4,4,500),0)
        self.assertEqual(scouting_relay_bonus(self.db,1,2,4,4,500),0)

    def test_upgrade_status_reports_pending_and_complete(self):
        pending=upgrade_status(self.db,1,1,300)[0]
        self.assertTrue(pending["upgrading"])
        self.assertEqual(pending["upgrade_remaining_seconds"],100)
        finished=upgrade_status(self.db,1,1,401)[0]
        self.assertEqual(finished["level"],2)
        self.assertFalse(finished["upgrading"])
        self.assertEqual(finished["next_level"],3)

    def test_upgrade_costs_and_timers_increase(self):
        self.assertGreater(UPGRADE_COSTS[3]["metal"],UPGRADE_COSTS[2]["metal"])
        self.assertGreater(UPGRADE_SECONDS[3],UPGRADE_SECONDS[2])

    def test_max_level(self):
        self.db.execute("UPDATE ashfall_relay_upgrades SET level=2,finishes_at=400")
        status=upgrade_status(self.db,1,1,401)[0]
        self.assertEqual(status["level"],3)
        self.assertIsNone(status["next_level"])

if __name__=="__main__":
    unittest.main()
