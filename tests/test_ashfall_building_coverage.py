"""Regression tests for all-family ASHFALL artwork coverage."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ashfall_building_coverage import coverage, required_names, REGISTRY


class BuildingCoverageTests(unittest.TestCase):
    def test_each_family_has_fifty_distinct_stage_names(self):
        names = required_names("farm")
        self.assertEqual(len(names), 50)
        self.assertEqual(len(set(names)), 50)
        self.assertEqual(names[0], "farm-standard-01.webp")
        self.assertEqual(names[24], "farm-standard-25.webp")
        self.assertEqual(names[25], "farm-crystal-01.webp")
        self.assertEqual(names[49], "farm-crystal-25.webp")

    def test_empty_art_directory_reports_1400_missing(self):
        with tempfile.TemporaryDirectory() as folder:
            result = coverage(REGISTRY, Path(folder))
        self.assertEqual(result["buildings"], 28)
        self.assertEqual(result["expected"], 1400)
        self.assertEqual(result["valid"], 0)
        self.assertEqual(result["complete_families"], 0)
        self.assertEqual(len(result["families"]), 28)
        self.assertTrue(all(row["missing"] == 50 for row in result["families"]))

    def test_no_manual_skin_levels_in_required_names(self):
        for key in ("hq", "hospital", "alliance_support"):
            names = required_names(key)
            self.assertTrue(all("skin" not in name for name in names))


if __name__ == "__main__":
    unittest.main()
