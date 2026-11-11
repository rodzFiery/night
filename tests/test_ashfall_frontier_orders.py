"""ASHFALL 4.2 — frontier directive integrity."""
import unittest
from app.ashfall_frontier_orders import frontier_orders


class FrontierOrdersTests(unittest.TestCase):
    def test_fresh_haven_offers_reachable_sector(self):
        data = frontier_orders((8, 8), set(), {})
        self.assertEqual(data["reachable_total"], 8)
        self.assertEqual(data["orders"][0]["kind"], "EXPLORE")

    def test_saved_reachable_objective_has_priority(self):
        data = frontier_orders((8, 8), set(), {}, objective=(9, 8))
        self.assertEqual(data["orders"][0]["kind"], "OBJECTIVE")
        self.assertEqual((data["orders"][0]["x"], data["orders"][0]["y"]), (9, 8))

    def test_unreachable_objective_not_advised(self):
        data = frontier_orders((8, 8), set(), {}, objective=(15, 15))
        self.assertTrue(all(order["kind"] != "OBJECTIVE" for order in data["orders"]))

    def test_active_mission_suspends_dispatch_advice(self):
        data = frontier_orders((8, 8), set(), {}, mission={"sector_x": 9})
        self.assertEqual(data["status"], "SCOUTS DEPLOYED")
        self.assertEqual(data["orders"], [])

    def test_unknown_sector_profiles_never_used(self):
        profiles = {(15, 15): {"resource_focus": "gas"}}
        data = frontier_orders((8, 8), set(), profiles)
        self.assertFalse(any(order["kind"] == "INTELLIGENCE" for order in data["orders"]))

    def test_fully_charted_world_has_no_frontier(self):
        all_cells = {(x, y) for x in range(16) for y in range(16)}
        data = frontier_orders((0, 0), all_cells, {})
        self.assertEqual(data["reachable_total"], 0)
        self.assertEqual(data["status"], "WORLD CHARTED")


if __name__ == "__main__":
    unittest.main()
