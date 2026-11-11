"""ASHFALL 4.1 — Frontier Legacy regression tests."""
import unittest
from app.ashfall_legacy import legacy_snapshot


class FrontierLegacyTests(unittest.TestCase):
    def test_fresh_haven_has_first_rank(self):
        result = legacy_snapshot((8, 8), set())
        self.assertEqual(result["rank"], 1)
        self.assertEqual(result["discoveries_remaining"], 3)
        self.assertEqual(result["unique_discoveries"], 0)

    def test_home_is_not_counted_twice(self):
        result = legacy_snapshot((8, 8), {(8, 8), (9, 8), (9, 8)})
        self.assertEqual(result["unique_discoveries"], 1)

    def test_unlocks_ranks_at_exact_thresholds(self):
        discovered = {(x, y) for y in range(16) for x in range(16) if (x, y) != (0, 0)}
        self.assertEqual(legacy_snapshot((0, 0), set(list(discovered)[:2]))["rank"], 1)
        self.assertEqual(legacy_snapshot((0, 0), set(list(discovered)[:3]))["rank"], 2)
        self.assertEqual(legacy_snapshot((0, 0), discovered)["rank"], 8)

    def test_full_completion(self):
        discovered = {(x, y) for y in range(16) for x in range(16)}
        result = legacy_snapshot((0, 0), discovered, 255)
        self.assertEqual(result["world_completion_percent"], 100)
        self.assertEqual(result["tier_progress_percent"], 100)
        self.assertIsNone(result["next_title"])

    def test_out_of_bounds_sectors_are_ignored(self):
        result = legacy_snapshot((0, 0), {(-1, 0), (16, 16), (0, 1)})
        self.assertEqual(result["unique_discoveries"], 1)

    def test_invalid_home_rejected(self):
        with self.assertRaises(ValueError):
            legacy_snapshot((16, 0), set())


if __name__ == "__main__":
    unittest.main()
