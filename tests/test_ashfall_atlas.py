"""ASHFALL 3.0 deterministic world atlas tests."""
import unittest
from app.ashfall_world import WORLD_SIZE, SECTOR_SIZE, sector_profile

class WorldAtlasTests(unittest.TestCase):
    def test_sector_grid_covers_world(self):
        self.assertEqual(WORLD_SIZE // SECTOR_SIZE, 16)

    def test_region_is_stable(self):
        self.assertEqual(sector_profile(1, 3, 4), sector_profile(1, 3, 4))

    def test_sector_bounds(self):
        region = sector_profile(1, 3, 4)
        self.assertEqual(region["bounds"]["x_min"], 384)
        self.assertEqual(region["bounds"]["x_max"], 511)
        self.assertEqual(region["bounds"]["y_min"], 512)
        self.assertEqual(region["bounds"]["y_max"], 639)

    def test_threat_is_bounded(self):
        for x in range(16):
            for y in range(16):
                region = sector_profile(1, x, y)
                self.assertGreaterEqual(region["threat"], 1)
                self.assertLessEqual(region["threat"], 5)

    def test_out_of_bounds_rejected(self):
        for x, y in [(-1, 0), (0, -1), (16, 0), (0, 16)]:
            with self.assertRaises(ValueError):
                sector_profile(1, x, y)

if __name__ == "__main__":
    unittest.main()
