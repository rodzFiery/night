"""Pure ASHFALL construction-planning invariants."""
import unittest
from app.ashfall_operations import construction_plan

def buildings():
    return {
        "hq": {"name": "Command Center", "level": 2, "next_level": 3,
               "unlocked": True, "cost": {"food": 200}, "seconds": 90},
        "farm": {"name": "Farm", "level": 1, "next_level": 2,
                 "unlocked": True, "cost": {"wood": 100}, "seconds": 40},
        "lumber": {"name": "Lumber Yard", "level": 1, "next_level": 2,
                   "unlocked": True, "cost": {"food": 100}, "seconds": 40},
        "salvage": {"name": "Salvage Station", "level": 1, "next_level": 2,
                    "unlocked": True, "cost": {"food": 100}, "seconds": 40},
        "fuel": {"name": "Fuel Collector", "level": 1, "next_level": 2,
                 "unlocked": True, "cost": {"food": 100}, "seconds": 40},
    }

class ConstructionPlannerTests(unittest.TestCase):
    def test_affordable_upgrade(self):
        plans = construction_plan(buildings(), {"food": 500, "wood": 200},
                                  {"food": 100, "wood": 50}, None, 100)
        farm = next(p for p in plans if p["key"] == "farm")
        self.assertEqual(farm["status"], "eligible")
        self.assertEqual(farm["estimated_wait_seconds"], 0)

    def test_shortage_estimate(self):
        plans = construction_plan(buildings(), {"food": 500, "wood": 50},
                                  {"food": 100, "wood": 50}, None, 100)
        farm = next(p for p in plans if p["key"] == "farm")
        self.assertEqual(farm["estimated_wait_seconds"], 3600)
        self.assertEqual(farm["missing"], {"wood": 50})

    def test_zero_production_has_no_eta(self):
        plans = construction_plan(buildings(), {"food": 500, "wood": 0},
                                  {"food": 100, "wood": 0}, None, 100)
        farm = next(p for p in plans if p["key"] == "farm")
        self.assertEqual(farm["status"], "needs_external_resources")
        self.assertIsNone(farm["estimated_wait_seconds"])

    def test_queue_waits_for_slot(self):
        plans = construction_plan(buildings(), {"food": 500, "wood": 200},
                                  {"food": 100, "wood": 50},
                                  {"finishes_at": 220}, 100)
        farm = next(p for p in plans if p["key"] == "farm")
        self.assertEqual(farm["status"], "queued_slot")
        self.assertEqual(farm["estimated_wait_seconds"], 120)

    def test_hq_requires_production(self):
        plans = construction_plan(buildings(), {"food": 500, "wood": 200},
                                  {"food": 100, "wood": 50}, None, 100)
        hq = next(p for p in plans if p["key"] == "hq")
        self.assertEqual(hq["status"], "eligible")
        changed = buildings()
        changed["hq"]["level"] = 3
        changed["hq"]["next_level"] = 4
        hq = next(p for p in construction_plan(
            changed, {"food": 500, "wood": 200},
            {"food": 100, "wood": 50}, None, 100
        ) if p["key"] == "hq")
        self.assertEqual(hq["status"], "requires_production")

if __name__ == "__main__":
    unittest.main()
