"""ASHFALL 3.2 reconnaissance duration and region invariants."""
import unittest
from app.ashfall_scouting import scout_duration
from app.ashfall_world import sector_profile

class ReconnaissanceTests(unittest.TestCase):
    def test_threat_duration_scale(self):
        self.assertEqual([scout_duration(t) for t in range(1, 6)],
                         [120, 150, 180, 210, 240])

    def test_sector_threat_is_eligible_for_duration(self):
        for x in range(16):
            for y in range(16):
                threat = sector_profile(1, x, y)["threat"]
                self.assertGreaterEqual(scout_duration(threat), 120)
                self.assertLessEqual(scout_duration(threat), 240)

if __name__ == "__main__":
    unittest.main()
