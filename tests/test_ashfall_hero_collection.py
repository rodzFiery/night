"""ASHFALL 7.2 collection chronicle regression coverage."""
import sqlite3
import unittest
from fastapi import HTTPException
from app.ashfall_hero_ascension import initialize,grant_fragments,progress,roster
from app.ashfall_hero_collection import snapshot,claim

class CollectionTests(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(":memory:");self.db.row_factory=sqlite3.Row
  self.db.executescript("""CREATE TABLE ashfall_havens(id INTEGER PRIMARY KEY);
  INSERT INTO ashfall_havens VALUES(1); INSERT INTO ashfall_havens VALUES(2);
  CREATE TABLE ashfall_heroes(haven_id INTEGER,hero_key TEXT,xp INTEGER,recruited_at REAL,
  PRIMARY KEY(haven_id,hero_key));""")
  initialize(self.db)
 def tearDown(self):self.db.close()
 def recruit(self,hid=1):
  grant_fragments(self.db,hid,"mara",10)
  progress(self.db,hid,"mara","unlock")
 def test_empty_collection(self):
  self.assertEqual(snapshot(self.db,1)["owned"],0)
  self.assertEqual(len(snapshot(self.db,1)["milestones"]),7)
 def test_collection_progress(self):
  self.recruit()
  self.assertEqual(snapshot(self.db,1)["completion_percent"],0.62)
  self.assertTrue(snapshot(self.db,1)["milestones"][0]["ready"])
 def test_unearned_reward_rejected(self):
  with self.assertRaises(HTTPException):claim(self.db,1,"first_blood",1000)
 def test_first_claim_awards_materials(self):
  self.recruit()
  claim(self.db,1,"first_blood",1000)
  self.assertEqual(roster(self.db,1)["materials"]["training_manual"],10)
 def test_duplicate_claim_rejected(self):
  self.recruit();claim(self.db,1,"first_blood",1000)
  with self.assertRaises(HTTPException):claim(self.db,1,"first_blood",1000)
 def test_haven_isolation(self):
  self.recruit()
  self.assertFalse(snapshot(self.db,2)["milestones"][0]["ready"])
 def test_unknown_milestone_rejected(self):
  with self.assertRaises(HTTPException):claim(self.db,1,"not_a_milestone",1000)
 def test_roster_exposes_collection(self):
  self.assertEqual(roster(self.db,1)["collection"]["total"],160)
 def test_gear_and_ranks_recorded(self):
  self.recruit()
  self.db.execute("INSERT INTO ashfall_hero_gear VALUES(1,'mara','head',0)")
  self.db.execute("INSERT INTO ashfall_hero_ranks VALUES(1,'mara',2)")
  self.assertEqual(snapshot(self.db,1)["equipment_crafted"],1)
  self.assertEqual(snapshot(self.db,1)["ranks_earned"],2)

if __name__=="__main__":unittest.main()
