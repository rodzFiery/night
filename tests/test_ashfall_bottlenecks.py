"""ASHFALL 2.7 resource bottleneck analysis regression tests."""
import unittest
from app.ashfall_operations import bottleneck_analysis

class BottleneckTests(unittest.TestCase):
    def test_no_shortages(self):
        self.assertEqual(bottleneck_analysis([
            {"status": "eligible", "missing": {}}
        ], {"food": 100}), [])

    def test_locked_upgrades_are_excluded(self):
        self.assertEqual(bottleneck_analysis([
            {"status": "requires_hq", "missing": {"gas": 500}}
        ], {"gas": 0}), [])

    def test_zero_production_is_external_supply(self):
        result = bottleneck_analysis([
            {"status": "needs_external_resources", "missing": {"gas": 20}}
        ], {"gas": 0})
        self.assertTrue(result[0]["requires_external_supply"])
        self.assertIsNone(result[0]["hours_to_cover_largest_deficit"])

    def test_largest_deficit_and_affected_count(self):
        result = bottleneck_analysis([
            {"status": "eligible", "missing": {"wood": 40}},
            {"status": "queued_slot", "missing": {"wood": 80}}
        ], {"wood": 40})
        self.assertEqual(result[0]["affected_upgrades"], 2)
        self.assertEqual(result[0]["largest_deficit"], 80)
        self.assertEqual(result[0]["hours_to_cover_largest_deficit"], 2)

    def test_external_shortage_precedes_passive_shortage(self):
        result = bottleneck_analysis([
            {"status": "eligible", "missing": {"wood": 500, "gas": 10}}
        ], {"wood": 50, "gas": 0})
        self.assertEqual(result[0]["resource"], "gas")

if __name__ == "__main__":
    unittest.main()
