"""ASHFALL 139 — headquarters art brief contract tests."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_ashfall_hq_briefs import brief, serialize, STANDARD, CRYSTAL


class HeadquartersArtBriefTests(unittest.TestCase):
    def test_all_fifty_stages_have_unique_signature(self):
        stages = [brief(i) for i in range(1, 51)]
        self.assertEqual(len(stages), 50)
        self.assertEqual(len({s["signature_feature"] for s in stages}), 50)
        self.assertEqual(len({s["filename"] for s in stages}), 50)
        self.assertTrue(all(s["production_status"] == "brief_only" for s in stages))

    def test_era_boundary(self):
        self.assertEqual(brief(25)["filename"], "hq-standard-25.webp")
        self.assertEqual(brief(26)["filename"], "hq-crystal-01.webp")
        self.assertEqual(brief(50)["filename"], "hq-crystal-25.webp")

    def test_no_visual_selector_or_automatic_approval(self):
        self.assertTrue(all(not brief(i)["approved"] for i in range(1, 51)))
        self.assertNotIn("skin", serialize().lower())

    def test_invalid_level_rejected(self):
        for level in (0, 51, -1):
            with self.assertRaises(ValueError):
                brief(level)


if __name__ == "__main__":
    unittest.main()
