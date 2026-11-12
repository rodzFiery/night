"""ASHFALL 8.0 — Grand Arsenal isolated progression and ownership tests."""
import sqlite3
import unittest
from fastapi import HTTPException
from app.ashfall_grand_arsenal import (CATALOG,initialize,grant,consume,balance,
 recipe,craft,enhance,equip,inventory)

class GrandArsenalTests(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(":memory:")
  self.db.execute("PRAGMA foreign_keys=ON")
  self.db.execute("CREATE TABLE ashfall_havens(id INTEGER PRIMARY KEY)")
  self.db.executemany("INSERT INTO ashfall_havens(id) VALUES(?)",[(1,),(2,)])
  initialize(self.db)
 def tearDown(self):self.db.close()
 def materials(self):
  for key in ("schematic","alloy","refinement_stone","crystal","core"):
   grant(self.db,1,"mat:"+key,10000)
 def test_catalog_scale(self):self.assertGreaterEqual(len(CATALOG),3000)
 def test_all_ids_unique(self):self.assertEqual(len(CATALOG),len(set(CATALOG)))
 def test_categories(self):
  self.assertTrue({"hero_gear","chief_gear","charm","research","event","material"}.issubset({i["category"] for i in CATALOG.values()}))
 def test_stacks_are_isolated(self):
  grant(self.db,1,"mat:alloy",15)
  self.assertEqual(balance(self.db,1,"mat:alloy"),15)
  self.assertEqual(balance(self.db,2,"mat:alloy"),0)
 def test_consume_cannot_overdraw(self):
  grant(self.db,1,"mat:alloy",2)
  with self.assertRaises(HTTPException):consume(self.db,1,"mat:alloy",3)
  self.assertEqual(balance(self.db,1,"mat:alloy"),2)
 def test_unknown_item_rejected(self):
  with self.assertRaises(HTTPException):grant(self.db,1,"not:real",1)
 def test_negative_grant_rejected(self):
  with self.assertRaises(HTTPException):grant(self.db,1,"mat:alloy",-1)
 def test_crafting_cost(self):
  self.assertIn("mat:alloy",recipe("hero:warden:head:1"))
 def test_crafting_requires_materials(self):
  with self.assertRaises(HTTPException):craft(self.db,1,"hero:warden:head:1")
 def test_craft_creates_instance(self):
  self.materials()
  craft(self.db,1,"hero:warden:head:1")
  self.assertEqual(inventory(self.db,1,"hero_gear")["total_records"],1)
 def test_enhancement_consumes_stones(self):
  self.materials()
  craft(self.db,1,"chief:warden:helmet:1")
  record=inventory(self.db,1,"chief_gear")["items"][0]
  result=enhance(self.db,1,record["instance_id"])
  self.assertEqual(result["enhancement"],1)
 def test_other_haven_cannot_enhance(self):
  self.materials();craft(self.db,1,"chief:warden:helmet:1")
  instance=inventory(self.db,1,"chief_gear")["items"][0]["instance_id"]
  with self.assertRaises(HTTPException):enhance(self.db,2,instance)
 def test_equipment_target_validation(self):
  self.materials();craft(self.db,1,"chief:warden:helmet:1")
  instance=inventory(self.db,1,"chief_gear")["items"][0]["instance_id"]
  with self.assertRaises(HTTPException):equip(self.db,1,instance,"hero:mara:head")
 def test_inventory_pagination(self):
  grant(self.db,1,"mat:alloy",1);grant(self.db,1,"mat:core",1)
  self.assertEqual(len(inventory(self.db,1,limit=1)["items"]),1)
 def test_stack_limit(self):
  with self.assertRaises(HTTPException):grant(self.db,1,"mat:alloy",100000001)
 def test_noncraftable_material(self):
  with self.assertRaises(HTTPException):recipe("mat:alloy")

if __name__=="__main__":unittest.main()
