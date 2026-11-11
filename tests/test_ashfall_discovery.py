"""ASHFALL 3.1 persistent atlas discovery schema regression tests."""
import sqlite3
import unittest
from app.ashfall_world import SECTOR_SIZE, sector_profile

class SectorDiscoveryTests(unittest.TestCase):
    def test_adjacent_sector_radius(self):
        home = (8, 8)
        nearby = [(x, y) for x in range(16) for y in range(16)
                  if max(abs(x-home[0]), abs(y-home[1])) <= 1]
        self.assertEqual(len(nearby), 9)
        self.assertNotIn((10, 8), nearby)

    def test_sector_coordinates_are_consistent(self):
        self.assertEqual(SECTOR_SIZE, 128)
        self.assertEqual(sector_profile(1, 8, 8)["bounds"]["x_min"], 1024)

    def test_unique_discovery_constraint(self):
        db = sqlite3.connect(":memory:")
        try:
            db.execute("""CREATE TABLE discoveries (
                haven_id INTEGER, sector_x INTEGER, sector_y INTEGER,
                PRIMARY KEY(haven_id,sector_x,sector_y))""")
            db.execute("INSERT INTO discoveries VALUES(1,8,8)")
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("INSERT INTO discoveries VALUES(1,8,8)")
            db.execute("INSERT INTO discoveries VALUES(2,8,8)")
            self.assertEqual(db.execute("SELECT COUNT(*) FROM discoveries").fetchone()[0],2)
        finally:
            db.close()

if __name__ == "__main__":
    unittest.main()
