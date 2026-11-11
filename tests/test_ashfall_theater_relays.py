"""ASHFALL 4.5 relay construction tests."""
import sqlite3
import unittest
from app.ashfall_theater_relays import theater_id,relay_snapshot,COST,BUILD_SECONDS

class RelayTests(unittest.TestCase):
    def test_theater_ids_are_stable(self):
        self.assertEqual(theater_id(0,0),"T-11")
        self.assertEqual(theater_id(3,3),"T-44")

    def test_invalid_theaters_rejected(self):
        for x,y in [(-1,0),(0,4),(4,0),(0,-1)]:
            with self.assertRaises(ValueError):theater_id(x,y)

    def test_cost_and_build_time_are_positive(self):
        self.assertTrue(all(value>0 for value in COST.values()))
        self.assertGreater(BUILD_SECONDS,0)

    def test_snapshot_tracks_construction_and_completion(self):
        db=sqlite3.connect(":memory:")
        db.row_factory=sqlite3.Row
        db.execute("""CREATE TABLE ashfall_theater_relays(
            haven_id INTEGER,state_id INTEGER,theater_x INTEGER,theater_y INTEGER,
            started_at REAL,finishes_at REAL)""")
        db.executescript("""CREATE TABLE ashfall_sector_discoveries(haven_id INTEGER,state_id INTEGER,sector_x INTEGER,sector_y INTEGER);
CREATE TABLE ashfall_world_positions(haven_id INTEGER,state_id INTEGER,x INTEGER,y INTEGER);""")
        db.execute("INSERT INTO ashfall_theater_relays VALUES(1,1,0,1,100,400)")
        building=relay_snapshot(db,1,1,200)["installations"][0]
        self.assertEqual(building["status"],"BUILDING")
        self.assertEqual(building["remaining_seconds"],200)
        finished=relay_snapshot(db,1,1,401)["installations"][0]
        self.assertEqual(finished["status"],"OPERATIONAL")

    def test_haven_and_state_isolation(self):
        db=sqlite3.connect(":memory:")
        db.row_factory=sqlite3.Row
        db.execute("""CREATE TABLE ashfall_theater_relays(
            haven_id INTEGER,state_id INTEGER,theater_x INTEGER,theater_y INTEGER,
            started_at REAL,finishes_at REAL)""")
        db.executescript("""CREATE TABLE ashfall_sector_discoveries(haven_id INTEGER,state_id INTEGER,sector_x INTEGER,sector_y INTEGER);
CREATE TABLE ashfall_world_positions(haven_id INTEGER,state_id INTEGER,x INTEGER,y INTEGER);""")
        db.execute("INSERT INTO ashfall_theater_relays VALUES(1,1,0,0,100,400)")
        self.assertEqual(relay_snapshot(db,2,1,200)["installations"],[])
        self.assertEqual(relay_snapshot(db,1,2,200)["installations"],[])

if __name__=="__main__":
    unittest.main()
