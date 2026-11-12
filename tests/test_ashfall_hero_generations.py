"""ASHFALL 7.0: sixteen generations, release gates and stat progression."""
import sqlite3
import unittest
from fastapi import HTTPException
from app.ashfall_hero_generations import CATALOG,stats,released_generation,is_released
from app.ashfall_hero_ascension import initialize,grant_fragments,progress,claim_reward,roster
from app.ashfall_heroes import HEROES
from app.ashfall_hero_mastery import SKILLS

class GenerationsTests(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(":memory:");self.db.row_factory=sqlite3.Row
  self.db.executescript("""CREATE TABLE ashfall_havens(id INTEGER PRIMARY KEY);
   INSERT INTO ashfall_havens VALUES(1);INSERT INTO ashfall_havens VALUES(2);
   CREATE TABLE ashfall_heroes(haven_id INTEGER,hero_key TEXT,xp INTEGER,recruited_at REAL,
   PRIMARY KEY(haven_id,hero_key));""")
  initialize(self.db)
 def tearDown(self):self.db.close()
 def test_160_distinct_heroes(self):self.assertEqual(len(CATALOG),160)
 def test_16_generations(self):
  self.assertEqual({h["generation"] for h in CATALOG.values()},set(range(1,17)))
 def test_10_per_generation(self):
  for g in range(1,17):self.assertEqual(sum(h["generation"]==g for h in CATALOG.values()),10)
 def test_four_rarities(self):
  self.assertEqual({h["rarity"] for h in CATALOG.values()},{"NORMAL","EPIC","LEGENDARY","SUPREME"})
 def test_original_heroes_preserved(self):
  self.assertEqual([CATALOG[k]["name"] for k in ("mara","kael","nyra","orion")],
   ["Mara Voss","Kael Rourke","Nyra Vale","Orion Ash"])
 def test_first_generation_open(self):
  self.assertEqual(released_generation(self.db,1),1)
 def test_future_generation_locked(self):
  self.assertFalse(is_released(self.db,1,"g02h01"))
  grant_fragments(self.db,1,"g02h01",10)
  with self.assertRaises(HTTPException):progress(self.db,1,"g02h01","unlock")
 def test_two_weekly_claims_release_second(self):
  claim_reward(self.db,1,"weekly",0)
  self.assertEqual(released_generation(self.db,1),1)
  claim_reward(self.db,1,"weekly",8*86400)
  self.assertEqual(released_generation(self.db,1),2)
  self.assertTrue(is_released(self.db,1,"g02h01"))
 def test_haven_release_isolation(self):
  claim_reward(self.db,1,"weekly",0);claim_reward(self.db,1,"weekly",8*86400)
  self.assertEqual(released_generation(self.db,2),1)
 def test_unlock_after_release(self):
  claim_reward(self.db,1,"weekly",0);claim_reward(self.db,1,"weekly",8*86400)
  grant_fragments(self.db,1,"g02h01",10)
  progress(self.db,1,"g02h01","unlock")
  self.assertTrue(any(h["key"]=="g02h01" and h["owned"] for h in roster(self.db,1)["heroes"]))
 def test_stat_fields(self):
  self.assertEqual(len(stats("mara")),14)
 def test_stat_growth(self):
  self.assertGreater(stats("mara",20,4)["attack"],stats("mara",1,0)["attack"])
 def test_gear_increases_stats(self):
  self.assertGreater(stats("mara",1,0,{"head":"SUPREME"})["attack"],stats("mara",1,0)["attack"])
 def test_every_hero_has_combat_definition(self):
  self.assertTrue(all(key in HEROES for key in CATALOG))
 def test_every_hero_has_mastery_skills(self):
  self.assertTrue(all(key in SKILLS for key in CATALOG))
 def test_roster_has_release_metadata(self):
  data=roster(self.db,1)
  self.assertEqual(data["total_heroes"],160)
  self.assertEqual(data["total_generations"],16)

if __name__=="__main__":unittest.main()
