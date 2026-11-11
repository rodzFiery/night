"""ASHFALL 6.0 hero ascension economy regression tests."""
import sqlite3
import unittest
from fastapi import HTTPException
from app.ashfall_hero_ascension import (
 initialize,grant,grant_fragments,roster,progress,claim_reward,
 RANK_STEPS,GEAR_TIERS,reward_period)

class HeroAscensionTests(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(":memory:")
  self.db.row_factory=sqlite3.Row
  self.db.executescript("""
   CREATE TABLE ashfall_havens(id INTEGER PRIMARY KEY);
   INSERT INTO ashfall_havens VALUES(1);
   INSERT INTO ashfall_havens VALUES(2);
   CREATE TABLE ashfall_heroes(haven_id INTEGER,hero_key TEXT,xp INTEGER,recruited_at REAL,
      PRIMARY KEY(haven_id,hero_key));
  """)
  initialize(self.db)
 def tearDown(self):self.db.close()
 def test_rank_budget_is_1200(self):self.assertEqual(sum(RANK_STEPS),1200)
 def test_seven_gear_tiers(self):self.assertEqual(len(GEAR_TIERS),7)
 def test_unlock_requires_ten_fragments(self):
  grant_fragments(self.db,1,"mara",9)
  with self.assertRaises(HTTPException):progress(self.db,1,"mara","unlock")
 def test_unlock_consumes_ten(self):
  grant_fragments(self.db,1,"mara",11)
  progress(self.db,1,"mara","unlock")
  self.assertEqual(roster(self.db,1)["heroes"][0]["fragments"],1)
 def test_rank_consumes_fragments(self):
  grant_fragments(self.db,1,"mara",20)
  progress(self.db,1,"mara","unlock")
  progress(self.db,1,"mara","rank")
  self.assertEqual(roster(self.db,1)["heroes"][0]["rank"],1)
  self.assertEqual(roster(self.db,1)["heroes"][0]["fragments"],0)
 def test_crafting_requires_material(self):
  grant_fragments(self.db,1,"mara",10)
  progress(self.db,1,"mara","unlock")
  with self.assertRaises(HTTPException):progress(self.db,1,"mara","craft","head")
 def test_crafting_consumes_material(self):
  grant_fragments(self.db,1,"mara",10);progress(self.db,1,"mara","unlock")
  grant(self.db,1,"scrap",10)
  progress(self.db,1,"mara","craft","head")
  self.assertEqual(roster(self.db,1)["heroes"][0]["gear"]["head"],"BASIC")
 def test_daily_claim_only_once(self):
  claim_reward(self.db,1,"daily",100000)
  with self.assertRaises(HTTPException):claim_reward(self.db,1,"daily",100000)
 def test_weekly_claim_only_once(self):
  claim_reward(self.db,1,"weekly",100000)
  with self.assertRaises(HTTPException):claim_reward(self.db,1,"weekly",100000)
 def test_haven_isolation(self):
  grant_fragments(self.db,1,"mara",10)
  self.assertEqual(roster(self.db,2)["heroes"][0]["fragments"],0)
 def test_periods_are_utc(self):
  self.assertEqual(reward_period(0,"daily"),"1970-01-01")
 def test_invalid_hero_rejected(self):
  with self.assertRaises(HTTPException):progress(self.db,1,"unknown","unlock")

if __name__=="__main__":unittest.main()
