"""ASHFALL 6.1: battle stats and event loot integration regression tests."""
import sqlite3
import unittest
from app.ashfall_heroes import bonus_for,ascension_combat_bonus
from app.ashfall_hero_ascension import initialize as init_ascension,grant_fragments,progress,roster
from app.ashfall_events import hero_event_rewards

class HeroCombatIntegrationTests(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(":memory:")
  self.db.row_factory=sqlite3.Row
  self.db.executescript("""
   CREATE TABLE ashfall_havens(id INTEGER PRIMARY KEY);
   INSERT INTO ashfall_havens VALUES(1); INSERT INTO ashfall_havens VALUES(2);
   CREATE TABLE ashfall_heroes(haven_id INTEGER,hero_key TEXT,xp INTEGER,recruited_at REAL,
      PRIMARY KEY(haven_id,hero_key));
   CREATE TABLE ashfall_hero_assignments(haven_id INTEGER PRIMARY KEY,hero_key TEXT);
  """)
  init_ascension(self.db)
  grant_fragments(self.db,1,"mara",20)
  progress(self.db,1,"mara","unlock")
  self.db.execute("INSERT INTO ashfall_hero_assignments VALUES(1,'mara')")
 def tearDown(self):self.db.close()
 def test_base_hero_bonus_preserved(self):
  self.assertAlmostEqual(bonus_for(self.db,1,"infantry"),.12)
 def test_rank_increases_real_combat_bonus(self):
  before=bonus_for(self.db,1,"infantry")
  progress(self.db,1,"mara","rank")
  self.assertAlmostEqual(bonus_for(self.db,1,"infantry")-before,.005)
 def test_gear_increases_real_combat_bonus(self):
  self.db.execute("INSERT INTO ashfall_hero_gear VALUES(1,'mara','head',0)")
  self.assertAlmostEqual(ascension_combat_bonus(self.db,1,"mara"),.002)
 def test_gear_multiple_tiers(self):
  self.db.execute("INSERT INTO ashfall_hero_gear VALUES(1,'mara','head',6)")
  self.assertAlmostEqual(ascension_combat_bonus(self.db,1,"mara"),.014)
 def test_other_haven_has_no_bonus(self):
  self.assertEqual(ascension_combat_bonus(self.db,2,"mara"),0)
 def test_event_awards_fragments_and_materials(self):
  reward=hero_event_rewards(self.db,1,"supply_drop","event")
  self.assertEqual(reward["quantity"],8)
  self.assertEqual(roster(self.db,1)["materials"]["scrap"],8)
  self.assertEqual(roster(self.db,1)["heroes"][0]["fragments"],12)
 def test_event_loot_isolated(self):
  hero_event_rewards(self.db,1,"cache","event")
  self.assertEqual(roster(self.db,2)["materials"],{})
 def test_unknown_event_no_loot(self):
  self.assertEqual(hero_event_rewards(self.db,1,"invalid","event"),{})
 def test_assigned_hero_visible_in_roster(self):
  self.assertEqual(roster(self.db,1)["assigned"],"mara")

if __name__=="__main__":unittest.main()
