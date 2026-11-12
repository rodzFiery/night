"""ASHFALL 140 — local HQ verification tests."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check_ashfall_hq_install as checker


class HeadquartersInstallTests(unittest.TestCase):
    def test_empty_install_reports_fifty_missing(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(checker, "ART", Path(folder)):
            result = checker.check()
        self.assertEqual(result["expected"], 50)
        self.assertEqual(result["present"], 0)
        self.assertEqual(result["verified"], 0)
        self.assertEqual(len(result["missing"]), 50)

    def test_level_names_span_both_eras(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(checker, "ART", Path(folder)):
            result = checker.check()
        names = [row["filename"] for row in result["stages"]]
        self.assertEqual(names[0], "hq-standard-01.webp")
        self.assertEqual(names[24], "hq-standard-25.webp")
        self.assertEqual(names[25], "hq-crystal-01.webp")
        self.assertEqual(names[49], "hq-crystal-25.webp")
        self.assertEqual(len(set(names)), 50)


if __name__ == "__main__":
    unittest.main()
