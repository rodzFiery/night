"""ASHFALL 5.2 doctrine and scouting integration tests."""
import sqlite3
import unittest
from app.ashfall_relay_doctrines import doctrine_bonus,doctrine_for,doctrine_snapshot,DOCTRINES
from app.ashfall_theater_relays import scouting_relay_bonus

class DoctrineTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(":memory:")
        self.db.row_factory=sqlite3.Row
        self.db.executescript("""
            CREATE TABLE ashfall_theater_relays(haven_id INTEGER,state_id INTEGER,theater_x INTEGER,theater_y INTEGER,started_at REAL,finishes_at REAL);
            CREATE TABLE ashfall_relay_upgrades(haven_id INTEGER,state_id INTEGER,theater_x INTEGER,theater_y INTEGER,level INTEGER,finishes_at REAL);
            CREATE TABLE ashfall_relay_doctrines(haven_id INTEGER,state_id INTEGER,theater_x INTEGER,theater_y INTEGER,doctrine TEXT,chosen_at REAL);
            INSERT INTO ashfall_theater_relays VALUES(1,1,0,0,100,200);
            INSERT INTO ashfall_relay_upgrades VALUES(1,1,0,0,1,250);
        """)

    def tearDown(self):
        self.db.close()

    def test_no_doctrine_without_selection(self):
        self.assertIsNone(doctrine_for(self.db,1,1,0,0))

    def test_level_two_unlocks_doctrine(self):
        result=doctrine_snapshot(self.db,1,1,300,{"wood":1000,"metal":1000,"gas":1000})
        self.assertTrue(result[0]["eligible"])
        self.assertEqual(len(result[0]["options"]),2)

    def test_level_one_cannot_choose(self):
        result=doctrine_snapshot(self.db,1,1,200,{"wood":1000,"metal":1000,"gas":1000})
        self.assertFalse(result[0]["eligible"])

    def test_exact_resource_shortage(self):
        result=doctrine_snapshot(self.db,1,1,300,{"wood":10,"metal":20,"gas":5})
        option=next(o for o in result[0]["options"] if o["key"]=="SURVEY")
        self.assertEqual(option["missing_resources"],{"wood":230,"metal":140,"gas":70})
        self.assertFalse(option["can_choose"])

    def test_survey_bonus_standalone(self):
        self.db.execute("INSERT INTO ashfall_relay_doctrines VALUES(1,1,0,0,'SURVEY',300)")
        self.assertEqual(scouting_relay_bonus(self.db,1,1,0,0,350),17)

    def test_signal_bonus_connected(self):
        self.db.execute("INSERT INTO ashfall_theater_relays VALUES(1,1,1,0,100,200)")
        self.db.execute("INSERT INTO ashfall_relay_doctrines VALUES(1,1,0,0,'SIGNAL',300)")
        self.assertEqual(scouting_relay_bonus(self.db,1,1,0,0,350),23)

    def test_signal_bonus_standalone(self):
        self.assertEqual(doctrine_bonus("SIGNAL",False),2)
        self.assertEqual(doctrine_bonus("SIGNAL",True),5)

    def test_foreign_haven_isolated(self):
        self.db.execute("INSERT INTO ashfall_relay_doctrines VALUES(2,1,0,0,'SURVEY',300)")
        self.assertEqual(scouting_relay_bonus(self.db,1,1,0,0,350),13)

    def test_selected_doctrine_is_not_available_again(self):
        self.db.execute("INSERT INTO ashfall_relay_doctrines VALUES(1,1,0,0,'SURVEY',300)")
        row=doctrine_snapshot(self.db,1,1,350,{"wood":1000,"metal":1000,"gas":1000})[0]
        self.assertFalse(row["eligible"])
        self.assertEqual(row["selected"],"SURVEY")

    def test_costs_are_positive(self):
        self.assertTrue(all(v>0 for d in DOCTRINES.values() for v in d["cost"].values()))

if __name__=="__main__":
    unittest.main()
