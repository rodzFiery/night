"""ASHFALL 2.0 regression tests: cooperative progression and SQLite integrity.
Run: python -m unittest discover -s tests -p test_ashfall_integrity.py -v
"""
import sqlite3
import unittest
from app.ashfall_alliances import initialize as alliances_init, upgrade_schema
from app.ashfall_alliance_progress import initialize as projects_init, snapshot as project_snapshot
from app.ashfall_alliance_technology import technology, production_bonus
from app.ashfall_economy import initialize as economy_init, snapshot as economy_snapshot

class AllianceIntegrityTests(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(":memory:")
  self.db.row_factory=sqlite3.Row
  self.db.execute("PRAGMA foreign_keys=ON")
  self.db.execute("CREATE TABLE users(id INTEGER PRIMARY KEY)")
  self.db.execute("CREATE TABLE ashfall_states(id INTEGER PRIMARY KEY)")
  self.db.execute("""CREATE TABLE ashfall_havens(
   id INTEGER PRIMARY KEY,user_id INTEGER REFERENCES users(id),
   state_id INTEGER REFERENCES ashfall_states(id),name TEXT,
   command_center_level INTEGER DEFAULT 1)""")
  self.db.executemany("INSERT INTO users(id) VALUES(?)",[(1,),(2,)])
  self.db.execute("INSERT INTO ashfall_states(id) VALUES(1)")
  self.db.executemany("INSERT INTO ashfall_havens(id,user_id,state_id,name) VALUES(?,?,1,?)",[(1,1,"Haven One"),(2,2,"Haven Two")])
  alliances_init(self.db)
  upgrade_schema(self.db)
  projects_init(self.db)
  economy_init(self.db)
  self.db.execute("INSERT INTO ashfall_alliances(state_id,name,tag,leader_haven_id,created_at) VALUES(1,'Wardens','WRD',1,0)")
  self.db.execute("INSERT INTO ashfall_alliance_members(haven_id,alliance_id,role,joined_at) VALUES(1,1,'leader',0)")
  self.db.execute("INSERT INTO ashfall_alliance_members(haven_id,alliance_id,role,joined_at) VALUES(2,1,'member',0)")
  self.db.commit()
 def tearDown(self):self.db.close()
 def test_membership_is_unique(self):
  with self.assertRaises(sqlite3.IntegrityError):
   self.db.execute("INSERT INTO ashfall_alliance_members(haven_id,alliance_id,role,joined_at) VALUES(1,1,'member',0)")
 def test_projects_start_empty(self):
  data=project_snapshot(self.db,1,1,1000)
  self.assertTrue(data["member"])
  self.assertEqual(len(data["projects"]),4)
  self.assertTrue(all(p["contributed"]==0 for p in data["projects"]))
 def test_completed_project_unlocks_bonus(self):
  self.db.execute("INSERT INTO ashfall_alliance_projects(alliance_id,project_key,contributed,completed_at) VALUES(1,'supply_network',1500,10)")
  self.db.execute("INSERT INTO ashfall_alliance_progress(alliance_id,xp) VALUES(1,2100)")
  self.assertEqual(technology(self.db,1)["level"],7)
  self.assertAlmostEqual(production_bonus(self.db,1,"food"),.15)
  self.assertEqual(production_bonus(self.db,1,"wood"),0)
 def test_no_alliance_means_no_bonus(self):
  self.db.execute("DELETE FROM ashfall_alliance_members WHERE haven_id=2")
  self.assertEqual(production_bonus(self.db,2,"food"),0)
 def test_leaderboard_aggregates(self):
  self.db.executemany("""INSERT INTO ashfall_alliance_contributions(
   alliance_id,haven_id,project_key,resource,amount,created_at) VALUES(1,?,'supply_network','food',?,0)""",[(1,100),(1,50),(2,80)])
  board=technology(self.db,1)["leaderboard"]
  self.assertEqual(board[0]["total"],150)
  self.assertEqual(board[1]["total"],80)
 def test_economy_creates_balances(self):
  data=economy_snapshot(self.db,1,1000)
  self.assertTrue(all(r in data["resources"] for r in ("food","wood","metal","gas")))
 def test_foreign_keys_block_orphan_members(self):
  with self.assertRaises(sqlite3.IntegrityError):
   self.db.execute("INSERT INTO ashfall_alliance_members(haven_id,alliance_id,role,joined_at) VALUES(999,1,'member',0)")

if __name__=="__main__":unittest.main()
