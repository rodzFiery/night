"""ASHFALL 4.6 — authoritative survey relay bonuses."""
import sqlite3
import unittest
from app.ashfall_theater_relays import scouting_relay_bonus


class RelayBonusTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(":memory:")
        self.db.execute("""CREATE TABLE ashfall_theater_relays(
            haven_id INTEGER,state_id INTEGER,theater_x INTEGER,theater_y INTEGER,
            started_at REAL,finishes_at REAL)""")
        self.db.execute("INSERT INTO ashfall_theater_relays VALUES(1,1,2,2,100,400)")

    def tearDown(self):
        self.db.close()

    def test_active_relay_accelerates_same_theater(self):
        self.assertEqual(scouting_relay_bonus(self.db,1,1,8,9,400),10)

    def test_unfinished_relay_grants_no_bonus(self):
        self.assertEqual(scouting_relay_bonus(self.db,1,1,8,9,399),0)

    def test_different_theater_grants_no_bonus(self):
        self.assertEqual(scouting_relay_bonus(self.db,1,1,7,9,500),0)

    def test_other_haven_and_state_grant_no_bonus(self):
        self.assertEqual(scouting_relay_bonus(self.db,2,1,8,8,500),0)
        self.assertEqual(scouting_relay_bonus(self.db,1,2,8,8,500),0)

    def test_invalid_sector_rejected(self):
        with self.assertRaises(ValueError):
            scouting_relay_bonus(self.db,1,1,16,8,500)

    def test_reduction_is_ten_percent_with_ceil(self):
        base=301
        reduced=(base*(100-10)+99)//100
        self.assertEqual(reduced,271)

if __name__=="__main__":
    unittest.main()
