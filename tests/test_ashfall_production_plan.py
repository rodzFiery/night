"""ASHFALL 131: contract tests for the production stage inventory."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_ashfall_production_plan import build_plan


class ProductionPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = build_plan()

    def test_exactly_fifty_unique_stages_per_building(self):
        rows = self.plan["stages"]
        self.assertEqual(len(rows), self.plan["counts"]["buildings"] * 50)
        for key in {row["building"] for row in rows}:
            stages = [row for row in rows if row["building"] == key]
            self.assertEqual({row["overall_level"] for row in stages}, set(range(1, 51)))
            self.assertEqual(len({row["filename"] for row in stages}), 50)

    def test_crystal_transition(self):
        rows = [row for row in self.plan["stages"] if row["building"] == "hq"]
        self.assertEqual((rows[24]["era"], rows[24]["era_level"]), ("standard", 25))
        self.assertEqual((rows[25]["era"], rows[25]["era_level"]), ("crystal", 1))
        self.assertEqual((rows[49]["era"], rows[49]["era_level"]), ("crystal", 25))

    def test_six_headquarters_benchmarks(self):
        benchmarks = [row["overall_level"] for row in self.plan["stages"]
                      if row["priority"] == "benchmark"]
        self.assertEqual(benchmarks, [1, 13, 25, 26, 38, 50])

    def test_manifest_is_not_fabricated(self):
        counts = self.plan["counts"]
        self.assertEqual(counts["published"] + counts["missing"], counts["required"])
        self.assertEqual(len({row["filename"] for row in self.plan["stages"]}),
                         counts["required"])


if __name__ == "__main__":
    unittest.main()
