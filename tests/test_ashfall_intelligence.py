"""ASHFALL 4.0 — operational intelligence and fog-of-war tests."""
import unittest
from app.ashfall_intelligence import frontier_intelligence


class FrontierIntelligenceTests(unittest.TestCase):
    def test_home_only_has_eight_reachable(self):
        result = frontier_intelligence((8, 8), set(), {})
        self.assertEqual(result["charted"], 1)
        self.assertEqual(result["reachable"], 8)
        self.assertIsNone(result["average_known_threat"])

    def test_world_corner_has_three_reachable(self):
        result = frontier_intelligence((0, 0), set(), {})
        self.assertEqual(result["reachable"], 3)

    def test_discovery_expands_frontier_without_duplicates(self):
        result = frontier_intelligence((8, 8), {(9, 8)}, {})
        self.assertEqual(result["charted"], 2)
        self.assertEqual(result["reachable"], 10)

    def test_only_known_profiles_contribute(self):
        profiles = {
            (8, 8): {"biome": "Ironwood", "resource_focus": "wood", "threat": 2},
            (9, 8): {"biome": "Ironwood", "resource_focus": "wood", "threat": 4},
            (15, 15): {"biome": "Secret", "resource_focus": "gas", "threat": 5},
        }
        result = frontier_intelligence((8, 8), {(9, 8)}, profiles)
        self.assertEqual(result["biomes"], {"Ironwood": 2})
        self.assertEqual(result["resource_focus"], {"wood": 2})
        self.assertEqual(result["average_known_threat"], 3)
        self.assertNotIn("Secret", result["biomes"])

    def test_all_world_charted_has_no_frontier(self):
        known = {(x, y) for x in range(16) for y in range(16)}
        result = frontier_intelligence((0, 0), known, {})
        self.assertEqual(result["world_percent"], 100)
        self.assertEqual(result["reachable"], 0)


if __name__ == "__main__":
    unittest.main()
