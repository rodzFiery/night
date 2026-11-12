"""ASHFALL 7.1: armory set effects and verified operation claims."""
import sqlite3
import unittest
from fastapi import HTTPException
from app.ashfall_hero_ascension import initialize,grant,grant_fragments,progress,roster
from app.ashfall_hero_warfare import snapshot,tactical_bonus,battle_attributes
from app.ashfall_hero_operations import status,claim,period_bounds

class HeroExpansionTests(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(":memory:");self.db.row_factory=sqlite3.Row
  self.db.executescript("""
   CREATE TABLE ashfall_havens(id INTEGER PRIMARY KEY);
   INSERT INTO ashfall_havens VALUES(1);INSERT INTO ashfall_havens VALUES(2);
   CREATE TABLE ashfall_heroes(haven_id INTEGER,hero_key TEXT,xp INTEGER,recruited_at REAL,
     PRIMARY KEY(haven_id,hero_key));
   CREATE TABLE ashfall_event_claims(haven_id INTEGER,event_day TEXT,event_key TEXT,claimed_at REAL);
   CREATE TABLE ashfall_battle_reports(haven_id INTEGER,outcome TEXT,created_at REAL);
  """)
  initialize(self.db)
  grant_fragments(self.db,1,"mara",10);progress(self.db,1,"mara","unlock")
 def tearDown(self):self.db.close()
 def test_six_slots(self):self.assertEqual(len(roster(self.db,1)["heroes"][0]["gear"]),6)
 def test_gear_material_required(self):
  with self.assertRaises(HTTPException):progress(self.db,1,"mara","craft","artifact")
 def test_craft_weapon(self):
  grant(self.db,1,"scrap",10);progress(self.db,1,"mara","craft","weapon")
  self.assertEqual(roster(self.db,1)["heroes"][0]["gear"]["weapon"],"BASIC")
 def test_three_piece_set(self):
  for slot in ("head","body","boots"):
   self.db.execute("INSERT INTO ashfall_hero_gear VALUES(1,'mara',?,0)",(slot,))
  self.assertEqual(snapshot(self.db,1,"mara")["set_bonus_percent"],1.5)
 def test_six_piece_set(self):
  for slot in ("head","body","boots","gloves","weapon","artifact"):
   self.db.execute("INSERT INTO ashfall_hero_gear VALUES(1,'mara',?,0)",(slot,))
  self.assertEqual(snapshot(self.db,1,"mara")["set_bonus_percent"],4.5)
 def test_signature_specialty_only(self):
  self.assertGreater(tactical_bonus(self.db,1,"mara","infantry"),tactical_bonus(self.db,1,"mara","hunter"))
 def test_other_haven_no_bonus(self):self.assertEqual(tactical_bonus(self.db,2,"mara","infantry"),0)
 def test_operation_requires_events(self):
  with self.assertRaises(HTTPException):claim(self.db,1,"daily_scout",100000)
 def test_event_operation_claim(self):
  for i in range(2):
   self.db.execute("INSERT INTO ashfall_event_claims VALUES(1,'1970-01-02',?,?)",(str(i),100000+i))
  self.assertTrue(next(x for x in status(self.db,1,100000) if x["key"]=="daily_scout")["ready"])
  claim(self.db,1,"daily_scout",100000)
  self.assertEqual(roster(self.db,1)["materials"]["training_manual"],6)
  with self.assertRaises(HTTPException):claim(self.db,1,"daily_scout",100000)
 def test_weekly_battle_operation(self):
  for i in range(3):self.db.execute("INSERT INTO ashfall_battle_reports VALUES(1,'victory',?)",(100000+i,))
  claim(self.db,1,"weekly_campaign",100000)
  self.assertEqual(roster(self.db,1)["materials"]["skill_insignia"],3)
 def test_haven_claim_isolation(self):
  self.db.execute("INSERT INTO ashfall_event_claims VALUES(1,'1970-01-02','a',100000)")
  self.db.execute("INSERT INTO ashfall_event_claims VALUES(1,'1970-01-02','b',100001)")
  self.assertFalse(next(x for x in status(self.db,2,100000) if x["key"]=="daily_scout")["ready"])
 def test_battle_attributes_from_assigned_hero(self):
  self.db.execute("INSERT INTO ashfall_hero_assignments VALUES(1,'mara')")
  self.assertGreater(battle_attributes(self.db,1,"infantry")["attack"],0)
 def test_battle_attributes_unassigned(self):
  self.assertEqual(battle_attributes(self.db,2,"infantry")["attack"],0)
 def test_utc_week_boundary(self):
  start,end=period_bounds(100000,"weekly");self.assertEqual(end-start,7*86400)

if __name__=="__main__":unittest.main()
