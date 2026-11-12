"""ASHFALL 7.5 signature progression regression tests."""
import sqlite3
import unittest
from app.ashfall_hero_generations import CATALOG
from app.ashfall_hero_ascension import initialize,grant_fragments,progress
from app.ashfall_hero_warfare import signature_identity,snapshot,tactical_bonus

class SignatureProgressionTests(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(":memory:");self.db.row_factory=sqlite3.Row
  self.db.executescript("""CREATE TABLE ashfall_havens(id INTEGER PRIMARY KEY);
  INSERT INTO ashfall_havens VALUES(1);INSERT INTO ashfall_havens VALUES(2);
  CREATE TABLE ashfall_heroes(haven_id INTEGER,hero_key TEXT,xp INTEGER,recruited_at REAL,
   PRIMARY KEY(haven_id,hero_key));""")
  initialize(self.db)
  grant_fragments(self.db,1,"mara",20)
  progress(self.db,1,"mara","unlock")
 def tearDown(self):self.db.close()
 def test_all_heroes_have_signature_identity(self):
  self.assertEqual(len(CATALOG),160)
  for hero in CATALOG.values():
   identity=signature_identity(hero)
   self.assertTrue(identity["name"])
   self.assertIn(identity["tier"],(1,2,3))
 def test_signature_generation_variants(self):
  a=signature_identity(CATALOG["g02h01"])
  b=signature_identity(CATALOG["g16h01"])
  self.assertNotEqual(a["name"],b["name"])
  self.assertGreater(b["tier"],a["tier"])
 def test_original_signature_is_backward_compatible(self):
  self.assertEqual(snapshot(self.db,1,"mara")["signature_bonus_percent"],1.2)
 def test_rank_scaling_increases_signature(self):
  before=snapshot(self.db,1,"mara")["signature_bonus_percent"]
  progress(self.db,1,"mara","rank")
  self.assertGreater(snapshot(self.db,1,"mara")["signature_bonus_percent"],before)
 def test_only_matching_class_receives_signature(self):
  self.assertGreater(tactical_bonus(self.db,1,"mara","infantry"),tactical_bonus(self.db,1,"mara","rider"))
 def test_unowned_hero_never_grants_signature(self):
  self.assertEqual(tactical_bonus(self.db,2,"mara","infantry"),0)
 def test_high_generation_scaling_is_capped(self):
  for hero in CATALOG.values():
   identity=signature_identity(hero)
   self.assertLessEqual(identity["tier"],3)
 def test_identity_description_is_present(self):
  for hero in CATALOG.values():self.assertTrue(signature_identity(hero)["description"])

if __name__=="__main__":unittest.main()
