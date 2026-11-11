"""ASHFALL 3.5 exploration campaign regression tests."""
import unittest
from app.ashfall_campaigns import campaign_snapshot

class ExplorationCampaignTests(unittest.TestCase):
    def test_new_haven_has_four_chapters(self):
        data=campaign_snapshot(1,8,8,set(),[])
        self.assertEqual(data["total_chapters"],4)
        self.assertEqual(data["completed_chapters"],0)
        self.assertTrue(data["chapters"][0]["unlocked"])
        self.assertFalse(data["chapters"][1]["unlocked"])

    def test_first_contact_requires_survey_and_archived_mission(self):
        seen={(8,7)}
        data=campaign_snapshot(1,8,8,seen,[])
        self.assertFalse(data["chapters"][0]["complete"])
        data=campaign_snapshot(1,8,8,seen,[(8,7)])
        self.assertTrue(data["chapters"][0]["complete"])
        self.assertTrue(data["chapters"][1]["unlocked"])

    def test_repeated_missions_do_not_inflate_progress(self):
        data=campaign_snapshot(1,8,8,{(8,7)},[(8,7),(8,7)])
        self.assertEqual(data["chapters"][0]["objectives"][1]["current"],1)

    def test_home_sector_does_not_count(self):
        data=campaign_snapshot(1,8,8,{(8,8)},[])
        self.assertEqual(data["chapters"][0]["objectives"][0]["current"],0)

    def test_edge_haven_uses_three_neighbors(self):
        seen={(0,1),(1,0),(1,1)}
        data=campaign_snapshot(1,0,0,seen,[])
        local=next(g for g in data["chapters"][-1]["objectives"] if g["key"]=="local_chart")
        self.assertEqual(local["target"],3)
        self.assertTrue(local["complete"])

if __name__=="__main__":
    unittest.main()
