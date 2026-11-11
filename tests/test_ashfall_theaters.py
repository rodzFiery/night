"""ASHFALL 4.3 — theater cartography regression tests."""
import unittest
from app.ashfall_theaters import theater_snapshot


class TheaterTests(unittest.TestCase):
    def test_world_divides_into_sixteen_theaters(self):
        report = theater_snapshot((8,8),set(),{})
        self.assertEqual(len(report["theaters"]),16)
        self.assertTrue(all(t["total"]==16 for t in report["theaters"]))

    def test_home_is_charted_without_discovery(self):
        report = theater_snapshot((8,8),set(),{})
        self.assertEqual(sum(t["charted"] for t in report["theaters"]),1)
        self.assertEqual(sum(t["contains_home"] for t in report["theaters"]),1)

    def test_unknown_theater_never_leaks_profile(self):
        profiles={(15,15):{"biome":"Secret","resource_focus":"gas","threat":5}}
        report=theater_snapshot((0,0),set(),profiles)
        target=next(t for t in report["theaters"] if t["origin"]=={"x":12,"y":12})
        self.assertEqual(target["status"],"UNSURVEYED")
        self.assertIsNone(target["known_biome"])
        self.assertIsNone(target["average_known_threat"])

    def test_known_profile_only(self):
        profiles={(0,0):{"biome":"Ironwood","resource_focus":"wood","threat":2},
                  (1,0):{"biome":"Ash Wastes","resource_focus":"metal","threat":4}}
        report=theater_snapshot((0,0),{(1,0)},profiles)
        target=report["theaters"][0]
        self.assertEqual(target["charted"],2)
        self.assertEqual(target["average_known_threat"],3)

    def test_complete_world_is_fully_charted(self):
        cells={(x,y) for x in range(16) for y in range(16)}
        report=theater_snapshot((0,0),cells,{})
        self.assertTrue(all(t["completion_percent"]==100 for t in report["theaters"]))
        self.assertTrue(all(t["status"]=="SECURED INTELLIGENCE" for t in report["theaters"]))


if __name__=="__main__":
    unittest.main()
