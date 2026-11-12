"""ASHFALL 6.2 mastery progression and battle integrity."""
import sqlite3
import unittest
from fastapi import HTTPException
from app.ashfall_hero_ascension import initialize,grant,grant_fragments,progress,roster
from app.ashfall_hero_mastery import train,combat_bonus,skill_cost
from app.ashfall_heroes import bonus_for

class HeroMasteryTests(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(":memory:");self.db.row_factory=sqlite3.Row
  self.db.executescript("""CREATE TABLE ashfall_havens(id INTEGER PRIMARY KEY);
  INSERT INTO ashfall_havens VALUES(1);INSERT INTO ashfall_havens VALUES(2);
  CREATE TABLE ashfall_heroes(haven_id INTEGER,hero_key TEXT,xp INTEGER,recruited_at REAL,PRIMARY KEY(haven_id,hero_key));""")
  initialize(self.db)
  grant_fragments(self.db,1,"mara",20)
  progress(self.db,1,"mara","unlock")
 def tearDown(self):self.db.close()
 def test_requires_manuals(self):
  with self.assertRaises(HTTPException):train(self.db,1,"mara",0)
 def test_training_consumes_manuals(self):
  grant(self.db,1,"training_manual",3)
  self.assertEqual(train(self.db,1,"mara",0),1)
  self.assertEqual(roster(self.db,1)["materials"]["training_manual"],0)
 def test_training_improves_combat(self):
  self.db.execute("INSERT INTO ashfall_hero_assignments VALUES(1,'mara')")
  before=bonus_for(self.db,1,"infantry")
  grant(self.db,1,"training_manual",3);train(self.db,1,"mara",0)
  self.assertAlmostEqual(bonus_for(self.db,1,"infantry")-before,.008)
 def test_specialty_does_not_apply_to_other_units(self):
  grant(self.db,1,"training_manual",3);train(self.db,1,"mara",0)
  self.assertEqual(combat_bonus(self.db,1,"mara","hunter"),0)
 def test_rank_gates_higher_levels(self):
  grant(self.db,1,"training_manual",100)
  self.assertEqual(train(self.db,1,"mara",0),1)
  self.assertEqual(train(self.db,1,"mara",0),2)
  with self.assertRaises(HTTPException):train(self.db,1,"mara",0)
 def test_unowned_hero_cannot_train(self):
  grant(self.db,1,"training_manual",100)
  with self.assertRaises(HTTPException):train(self.db,1,"nyra",0)
 def test_invalid_skill_rejected(self):
  with self.assertRaises(HTTPException):train(self.db,1,"mara",2)
 def test_other_haven_isolation(self):
  grant(self.db,1,"training_manual",3);train(self.db,1,"mara",0)
  self.assertEqual(combat_bonus(self.db,2,"mara","infantry"),0)
 def test_rare_insignia_required_at_higher_level(self):
  self.assertEqual(skill_cost(0,4)["skill_insignia"],1)
 def test_two_skills_per_hero(self):
  self.assertEqual(len(roster(self.db,1)["heroes"][0]["skills"]),2)

if __name__=="__main__":unittest.main()
