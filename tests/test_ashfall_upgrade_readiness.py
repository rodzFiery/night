"""ASHFALL 5.1: industrial upgrade affordability and UI readiness tests."""
import sqlite3
import unittest
from unittest.mock import patch
from app.ashfall_relay_upgrades import upgrade_readiness

class UpgradeReadinessTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(":memory:")
        self.db.row_factory=sqlite3.Row
        self.db.executescript("""
            CREATE TABLE ashfall_theater_relays(haven_id INTEGER,state_id INTEGER,theater_x INTEGER,theater_y INTEGER,started_at REAL,finishes_at REAL);
            CREATE TABLE ashfall_relay_upgrades(haven_id INTEGER,state_id INTEGER,theater_x INTEGER,theater_y INTEGER,level INTEGER,finishes_at REAL);
            INSERT INTO ashfall_theater_relays VALUES(1,1,0,0,100,200);
        """)

    def tearDown(self):
        self.db.close()

    def readiness(self,wood=1000,metal=1000,gas=1000,now=300):
        with patch("app.ashfall_economy.snapshot",return_value={"resources":{"wood":wood,"metal":metal,"gas":gas}}):
            return upgrade_readiness(self.db,1,1,now)[0]

    def test_ready_when_affordable(self):
        self.assertTrue(self.readiness()["can_upgrade"])

    def test_missing_resources_are_exact(self):
        row=self.readiness(wood=50,metal=10,gas=0)
        self.assertEqual(row["readiness_reason"],"INSUFFICIENT RESOURCES")
        self.assertEqual(row["missing_resources"],{"wood":250,"metal":170,"gas":60})

    def test_unfinished_relay_cannot_upgrade(self):
        self.db.execute("UPDATE ashfall_theater_relays SET finishes_at=500")
        self.assertEqual(self.readiness()["readiness_reason"],"RELAY CONSTRUCTING")

    def test_pending_upgrade_cannot_repeat(self):
        self.db.execute("INSERT INTO ashfall_relay_upgrades VALUES(1,1,0,0,1,500)")
        self.assertEqual(self.readiness()["readiness_reason"],"UPGRADE IN PROGRESS")

    def test_maximum_level_blocks_upgrade(self):
        self.db.execute("INSERT INTO ashfall_relay_upgrades VALUES(1,1,0,0,2,250)")
        row=self.readiness()
        self.assertEqual(row["level"],3)
        self.assertEqual(row["readiness_reason"],"MAX LEVEL")

    def test_foreign_haven_not_included(self):
        self.db.execute("INSERT INTO ashfall_theater_relays VALUES(2,1,1,1,100,200)")
        with patch("app.ashfall_economy.snapshot",return_value={"resources":{"wood":1000,"metal":1000,"gas":1000}}):
            result=upgrade_readiness(self.db,1,1,300)
        self.assertEqual(len(result),1)

if __name__=="__main__":
    unittest.main()
