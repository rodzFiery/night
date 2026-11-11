"""ASHFALL 4.8 — linked relay network integration tests."""
import sqlite3
import unittest
from app.ashfall_theater_relays import scouting_relay_bonus,relay_network_snapshot

class RelayNetworkTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(":memory:")
        self.db.row_factory=sqlite3.Row
        self.db.execute("""CREATE TABLE ashfall_theater_relays(
            haven_id INTEGER,state_id INTEGER,theater_x INTEGER,theater_y INTEGER,
            started_at REAL,finishes_at REAL)""")
        self.db.executescript("""CREATE TABLE ashfall_sector_discoveries(haven_id INTEGER,state_id INTEGER,sector_x INTEGER,sector_y INTEGER);
CREATE TABLE ashfall_world_positions(haven_id INTEGER,state_id INTEGER,x INTEGER,y INTEGER);""")
        self.db.execute("INSERT INTO ashfall_theater_relays VALUES(1,1,1,1,100,200)")

    def add(self,x,y,finish=200,haven=1,state=1):
        self.db.execute("INSERT INTO ashfall_theater_relays VALUES(?,?,?,?,100,?)",
                        (haven,state,x,y,finish))

    def tearDown(self):
        self.db.close()

    def test_standalone_relay_is_ten_percent(self):
        self.assertEqual(scouting_relay_bonus(self.db,1,1,4,4,300),10)

    def test_orthogonal_connection_is_fifteen_percent(self):
        self.add(2,1)
        self.assertEqual(scouting_relay_bonus(self.db,1,1,4,4,300),15)
        self.assertEqual(scouting_relay_bonus(self.db,1,1,8,4,300),15)

    def test_diagonal_connection_does_not_count(self):
        self.add(2,2)
        self.assertEqual(scouting_relay_bonus(self.db,1,1,4,4,300),10)

    def test_unfinished_neighbor_does_not_count(self):
        self.add(2,1,finish=500)
        self.assertEqual(scouting_relay_bonus(self.db,1,1,4,4,300),10)

    def test_foreign_haven_neighbor_does_not_count(self):
        self.add(2,1,haven=2)
        self.assertEqual(scouting_relay_bonus(self.db,1,1,4,4,300),10)

    def test_foreign_state_neighbor_does_not_count(self):
        self.add(2,1,state=2)
        self.assertEqual(scouting_relay_bonus(self.db,1,1,4,4,300),10)

    def test_bonus_does_not_stack_above_fifteen(self):
        self.add(2,1)
        self.add(0,1)
        self.add(1,2)
        self.assertEqual(scouting_relay_bonus(self.db,1,1,4,4,300),15)

    def test_network_snapshot_counts_linked_relays(self):
        self.add(2,1)
        report=relay_network_snapshot(self.db,1,1,300)
        self.assertEqual(report["operational_relays"],2)
        self.assertEqual(report["linked_relays"],2)
        self.assertEqual(report["linked_theaters"],["T-22","T-32"])

if __name__=="__main__":
    unittest.main()
