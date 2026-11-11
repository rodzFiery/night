"""ASHFALL 2.8 strategic path milestone tests."""
import unittest
from app.ashfall_operations import development_paths

class DevelopmentPathTests(unittest.TestCase):
    def test_empty_haven_has_three_incomplete_tracks(self):
        paths = development_paths({}, {}, 0, 0, [])
        self.assertEqual(len(paths), 3)
        self.assertTrue(all(path["percent"] == 0 for path in paths))
        self.assertTrue(all(path["advisory_only"] for path in paths))

    def test_industrial_milestones_reflect_buildings_and_marches(self):
        buildings = {key: {"level": level} for key, level in
                     {"farm": 2, "lumber": 2, "salvage": 1, "fuel": 1}.items()}
        paths = development_paths(buildings, {}, 0, 1, [])
        industry = next(p for p in paths if p["key"] == "economy")
        self.assertEqual(industry["completed"], industry["total"])
        self.assertEqual(industry["percent"], 100)
        self.assertIsNone(industry["next_goal"])

    def test_military_requires_troops_as_well_as_buildings(self):
        paths = development_paths({"barracks": {"level": 2}, "hq": {"level": 3}},
                                  {}, 19, 0, [])
        military = next(p for p in paths if p["key"] == "military")
        self.assertEqual(military["completed"], 2)
        self.assertEqual(military["total"], 3)
        self.assertEqual(military["next_goal"], "Stationed troops")

    def test_science_uses_technology_levels(self):
        tech = {key: {"level": level} for key, level in
                {"agriculture": 2, "forestry": 2, "metallurgy": 1,
                 "fuel_processing": 1}.items()}
        paths = development_paths({}, tech, 0, 0, [])
        science = next(p for p in paths if p["key"] == "science")
        self.assertEqual(science["percent"], 100)

if __name__ == "__main__":
    unittest.main()
