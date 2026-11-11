"""ASHFALL 4.7 — construction eligibility integration tests."""
import sqlite3
import unittest
from unittest.mock import patch
from app.ashfall_theater_relays import relay_build_readiness


class RelayReadinessTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(":memory:")
        self.db.row_factory=sqlite3.Row
        self.db.executescript("""
            CREATE TABLE ashfall_world_positions(haven_id INTEGER,state_id INTEGER,x INTEGER,y INTEGER);
            CREATE TABLE ashfall_sector_discoveries(haven_id INTEGER,state_id INTEGER,sector_x INTEGER,sector_y INTEGER);
            CREATE TABLE ashfall_theater_relays(haven_id INTEGER,state_id INTEGER,theater_x INTEGER,theater_y INTEGER);
            INSERT INTO ashfall_world_positions VALUES(1,1,1024,1024);
            INSERT INTO ashfall_world_positions VALUES(2,1,128,128);
            INSERT INTO ashfall_sector_discoveries VALUES(1,1,1,1);
            INSERT INTO ashfall_theater_relays VALUES(1,1,0,0);
        """)
        self.economy=patch("app.ashfall_economy.snapshot",return_value={
            "resources":{"wood":300,"metal":200,"gas":50}})
        self.economy.start()

    def tearDown(self):
        self.economy.stop()
        self.db.close()

    def test_home_theater_can_build(self):
        result=relay_build_readiness(self.db,1,1,100)
        self.assertTrue(next(r for r in result if r["id"]=="T-33")["can_build"])

    def test_existing_relay_cannot_be_built_again(self):
        result=relay_build_readiness(self.db,1,1,100)
        self.assertEqual(result[0]["reason"],"ALREADY BUILT")

    def test_uncharted_theater_rejected(self):
        result=relay_build_readiness(self.db,1,1,100)
        self.assertEqual(next(r for r in result if r["id"]=="T-44")["reason"],"THEATER UNCHARTED")

    def test_insufficient_resources_reported(self):
        with patch("app.ashfall_economy.snapshot",return_value={"resources":{"wood":10,"metal":0,"gas":0}}):
            result=relay_build_readiness(self.db,1,1,100)
        home=next(r for r in result if r["id"]=="T-33")
        self.assertEqual(home["reason"],"INSUFFICIENT RESOURCES")
        self.assertEqual(home["missing_resources"],{"wood":170,"metal":100,"gas":25})

    def test_other_haven_does_not_inherit_discoveries(self):
        result=relay_build_readiness(self.db,2,1,100)
        self.assertEqual(result[0]["reason"],"READY")
        self.assertEqual(next(r for r in result if r["id"]=="T-33")["reason"],"THEATER UNCHARTED")

    def test_sixteen_theaters(self):
        self.assertEqual(len(relay_build_readiness(self.db,1,1,100)),16)


if __name__=="__main__":
    unittest.main()
