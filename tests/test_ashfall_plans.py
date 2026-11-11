"""ASHFALL 3.9 expedition snapshot regression tests."""
import unittest
from app.ashfall_plans import plan_snapshot


class ExpeditionPlanTests(unittest.TestCase):
    def test_unexplored_route(self):
        result = plan_snapshot((2, 2), (4, 2), set(), 100)
        self.assertEqual(result["target"], {"x": 4, "y": 2})
        self.assertEqual(result["total_steps"], 2)
        self.assertEqual(result["charted_steps"], 0)
        self.assertEqual(result["progress_percent"], 0)
        self.assertFalse(result["complete"])

    def test_progress_updates_after_discovery(self):
        result = plan_snapshot((2, 2), (4, 2), {(3, 2)}, 100)
        self.assertEqual(result["charted_steps"], 1)
        self.assertEqual(result["progress_percent"], 50)
        self.assertFalse(result["complete"])

    def test_complete_route(self):
        result = plan_snapshot((2, 2), (4, 2), {(3, 2), (4, 2)}, 100)
        self.assertTrue(result["complete"])
        self.assertEqual(result["progress_percent"], 100)

    def test_home_destination(self):
        result = plan_snapshot((2, 2), (2, 2), set(), 100)
        self.assertEqual(result["total_steps"], 0)
        self.assertTrue(result["complete"])
        self.assertEqual(result["progress_percent"], 100)

    def test_rejects_invalid_coordinates(self):
        with self.assertRaises(ValueError):
            plan_snapshot((2, 2), (16, 2), set(), 100)


if __name__ == "__main__":
    unittest.main()
