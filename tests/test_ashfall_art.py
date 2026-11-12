"""ASHFALL production-art import and audit smoke tests.

Run from repo root: python -m unittest discover -s tests -p 'test_ashfall_art.py'
Pillow-dependent import test is skipped if Pillow is unavailable.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/import_ashfall_art.py"
AUDIT = ROOT / "scripts/audit_ashfall_art.py"


def load_audit():
    spec = importlib.util.spec_from_file_location("ashfall_art_audit", AUDIT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class AssetContractTests(unittest.TestCase):
    def test_registry_contains_unique_buildings(self):
        audit = load_audit()
        entries = audit.ENTRY.findall(audit.REGISTRY.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(entries), 28)
        self.assertEqual(len({entry[0] for entry in entries}), len(entries))

    def test_asset_matrix_has_fifty_stages_per_building(self):
        report = load_audit().audit(512, 384)
        self.assertEqual(report["expected"], len(load_audit().ENTRY.findall(load_audit().REGISTRY.read_text(encoding="utf-8"))) * 50)
        self.assertEqual(report["present"] + report["missing"], report["expected"])

    def test_identical_artwork_cannot_fill_two_levels(self):
        audit = load_audit()
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory:
            original = audit.ART
            try:
                audit.ART = Path(directory)
                sample = b"RIFF" + (22).to_bytes(4, "little") + b"WEBP" + b"VP8X" + b"\\x0a\\x00\\x00\\x00" + b"\\x00" * 4 + (767).to_bytes(3, "little") + (767).to_bytes(3, "little")
                (audit.ART / "hq-standard-01.webp").write_bytes(sample)
                (audit.ART / "hq-standard-02.webp").write_bytes(sample)
                report = audit.audit(512, 384)
                self.assertTrue(any("identical artwork" in p["issue"] for p in report["problems"]))
                self.assertEqual(report["distinct_verified_assets"], 1)
            finally:
                audit.ART = original

    def test_unknown_building_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--input", str(Path(directory) / "none.png"),
                 "--building", "not_a_building", "--level", "1"],
                capture_output=True, text=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unknown building", result.stderr)

    def test_bad_level_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--input", str(Path(directory) / "none.png"),
                 "--building", "hq", "--level", "51"],
                capture_output=True, text=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Levels must be unique", result.stderr)

    @unittest.skipUnless(importlib.util.find_spec("PIL"), "Pillow not installed")
    def test_opaque_screenshot_rejected(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "opaque.png"
            Image.new("RGB", (512, 512), "#334455").save(source)
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--input", str(source),
                 "--building", "hq", "--level", "1"],
                capture_output=True, text=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("alpha channel", result.stderr)


if __name__ == "__main__":
    unittest.main()
