"""ASHFALL 2.6 investment comparison tests."""
import unittest
from app.ashfall_operations import investment_analysis

class InvestmentAnalysisTests(unittest.TestCase):
    def test_level_one_increment_uses_existing_effective_rate(self):
        plans = [{"key": "farm", "name": "Farm", "cost": {"wood": 100},
                  "status": "eligible", "estimated_wait_seconds": 0}]
        buildings = {"farm": {"level": 1}}
        result = investment_analysis(plans, buildings, {"food": 120}, {"food": 1})
        self.assertAlmostEqual(result[0]["additional_per_hour"], 21.6)
        self.assertAlmostEqual(result[0]["output_per_100_cost_units"], 21.6)

    def test_level_zero_uses_research_and_alliance_multiplier(self):
        plans = [{"key": "fuel", "name": "Fuel Collector",
                  "cost": {"food": 100, "wood": 100},
                  "status": "eligible", "estimated_wait_seconds": 0}]
        result = investment_analysis(plans, {"fuel": {"level": 0}},
                                     {"gas": 0}, {"gas": 1.2})
        self.assertEqual(result[0]["additional_per_hour"], 30)
        self.assertEqual(result[0]["output_per_100_cost_units"], 15)

    def test_non_production_buildings_are_excluded(self):
        plans = [{"key": "hq", "name": "Command Center", "cost": {"food": 100},
                  "status": "eligible", "estimated_wait_seconds": 0}]
        self.assertEqual(investment_analysis(plans, {}, {}, {}), [])

    def test_eligible_buildings_rank_before_locked(self):
        plans = [
            {"key": "farm", "name": "Farm", "cost": {"wood": 100},
             "status": "requires_hq", "estimated_wait_seconds": None},
            {"key": "lumber", "name": "Lumber Yard", "cost": {"food": 100},
             "status": "eligible", "estimated_wait_seconds": 0},
        ]
        result = investment_analysis(plans, {"farm": {"level": 1}, "lumber": {"level": 1}},
                                     {"food": 120, "wood": 100}, {"food": 1, "wood": 1})
        self.assertEqual(result[0]["key"], "lumber")

if __name__ == "__main__":
    unittest.main()
