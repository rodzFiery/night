"""Crystal Frontier integration tests against an in-memory SQLite database."""
import sqlite3
import unittest
from app import ashfall_crystal_frontier as frontier

class CrystalFrontierTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(":memory:")
        self.db.row_factory=sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("CREATE TABLE ashfall_havens(id INTEGER PRIMARY KEY,user_id INTEGER,state_id INTEGER)")
        self.db.execute("INSERT INTO ashfall_havens VALUES(1,1,1)")
        self.db.execute("CREATE TABLE ashfall_building_levels(haven_id INTEGER,building_key TEXT,level INTEGER CHECK(level BETWEEN 0 AND 55),PRIMARY KEY(haven_id,building_key))")
        self.db.execute("INSERT INTO ashfall_building_levels VALUES(1,'hq',30)")
        self.db.execute("CREATE TABLE ashfall_resource_balances(haven_id INTEGER PRIMARY KEY,food INTEGER,wood INTEGER,metal INTEGER,gas INTEGER)")
        self.db.execute("INSERT INTO ashfall_resource_balances VALUES(1,100000,100000,100000,100000)")
        frontier.initialize(self.db)
        frontier.ensure(self.db,1)
        self.db.execute("UPDATE ashfall_crystal_balances SET crystal_shards=10000,ancient_cores=1000,prismatic_essence=500 WHERE haven_id=1")
    def tearDown(self):
        self.db.close()
    def test_snapshot_and_catalog(self):
        data=frontier.snapshot(self.db,1,now=100)
        self.assertTrue(data["unlocked"])
        self.assertEqual(data["max_level"],55)
        self.assertEqual(len(data["mission_catalog"]),4)
        self.assertEqual(len(data["research"]),4)
    def test_mission_launch_and_claim_once(self):
        mission=frontier.launch(self.db,1,"fractured_quarry",now=100)
        with self.assertRaisesRegex(ValueError,"still underway"):
            frontier.claim(self.db,1,mission["mission_id"],now=101)
        before=frontier.crystal.balance(self.db,1)["crystal_shards"]
        reward=frontier.claim(self.db,1,mission["mission_id"],now=2000)
        self.assertEqual(frontier.crystal.balance(self.db,1)["crystal_shards"],before+reward["crystal_shards"])
        with self.assertRaisesRegex(ValueError,"already claimed"):
            frontier.claim(self.db,1,mission["mission_id"],now=2001)
    def test_three_mission_limit(self):
        for _ in range(3):frontier.launch(self.db,1,"fractured_quarry",now=100)
        with self.assertRaisesRegex(ValueError,"three expedition slots"):
            frontier.launch(self.db,1,"fractured_quarry",now=100)
    def test_research_prerequisite(self):
        with self.assertRaisesRegex(ValueError,"prerequisite"):
            frontier.upgrade_research(self.db,1,"crystal_refining",now=100)
        frontier.upgrade_research(self.db,1,"resonance_mapping",now=101)
        result=frontier.upgrade_research(self.db,1,"crystal_refining",now=102)
        self.assertEqual(result["level"],1)
    def test_refining_requires_research(self):
        with self.assertRaisesRegex(ValueError,"Research Crystal Refining"):
            frontier.refine(self.db,1,"core_synthesis",now=100)
        frontier.upgrade_research(self.db,1,"resonance_mapping",now=101)
        frontier.upgrade_research(self.db,1,"crystal_refining",now=102)
        before=frontier.crystal.balance(self.db,1)["ancient_cores"]
        reward=frontier.refine(self.db,1,"core_synthesis",now=103)
        self.assertEqual(frontier.crystal.balance(self.db,1)["ancient_cores"],before+reward["ancient_cores"])
    def test_locked_hq(self):
        self.db.execute("UPDATE ashfall_building_levels SET level=29 WHERE haven_id=1")
        with self.assertRaisesRegex(ValueError,"level too low"):
            frontier.launch(self.db,1,"fractured_quarry",now=100)
        with self.assertRaisesRegex(ValueError,"locked"):
            frontier.upgrade_research(self.db,1,"resonance_mapping",now=100)
    def test_claim_does_not_cross_havens(self):
        self.db.execute("INSERT INTO ashfall_havens VALUES(2,2,1)")
        self.db.execute("INSERT INTO ashfall_building_levels VALUES(2,'hq',30)")
        frontier.ensure(self.db,2)
        mission=frontier.launch(self.db,1,"fractured_quarry",now=100)
        with self.assertRaisesRegex(ValueError,"not found"):
            frontier.claim(self.db,2,mission["mission_id"],now=3000)

if __name__=="__main__":
    unittest.main()
