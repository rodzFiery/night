"""ASHFALL 3.3 Cartographer Mastery regression tests."""
import unittest
from app.ashfall_cartography import mastery_snapshot

class CartographyTests(unittest.TestCase):
    def test_empty_record_has_no_badges(self):
        data=mastery_snapshot(1,8,8,set())
        self.assertEqual(data["rank"],"Uncharted")
        self.assertEqual(data["local_percent"],0)
        self.assertFalse(any(b["earned"] for b in data["badges"]))

    def test_home_does_not_count_as_discovery(self):
        data=mastery_snapshot(1,8,8,{(8,8)})
        self.assertEqual(data["surveyed_total"],0)

    def test_first_survey_unlocks_first_signal(self):
        data=mastery_snapshot(1,8,8,{(8,7)})
        self.assertEqual(data["rank"],"Scout")
        self.assertTrue(data["badges"][0]["earned"])
        self.assertFalse(data["badges"][1]["earned"])

    def test_eight_neighbors_complete_region(self):
        seen={(x,y) for x in (7,8,9) for y in (7,8,9) if (x,y)!=(8,8)}
        data=mastery_snapshot(1,8,8,seen)
        self.assertEqual(data["local_percent"],100)
        self.assertEqual(data["rank"],"Regional Cartographer")
        self.assertTrue(all(b["earned"] for b in data["badges"][:4]))

    def test_world_edge_has_fewer_neighbors(self):
        data=mastery_snapshot(1,0,0,{(0,1),(1,0),(1,1)})
        self.assertEqual(data["local_total"],3)
        self.assertEqual(data["local_percent"],100)

    def test_biome_badge_is_grounded_in_sector(self):
        data=mastery_snapshot(1,8,8,{(8,7)})
        self.assertEqual(sum(data["biome_counts"].values()),1)
        self.assertEqual(sum(b["earned"] for b in data["badges"][4:]),1)

if __name__=="__main__":
    unittest.main()
