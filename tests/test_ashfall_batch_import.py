"""ASHFALL 136: safe batch stage importer tests."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from import_ashfall_batch import candidates


class BatchImportTests(unittest.TestCase):
    def test_maps_standard_and_crystal_to_unique_stage_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)
            (source / "hq-standard-01.png").write_bytes(b"test")
            (source / "hq-crystal-25.webp").write_bytes(b"test")
            stages, errors = candidates(source)
            self.assertFalse(errors)
            self.assertEqual({target.name for _, target in stages},
                             {"hq-standard-01.webp", "hq-crystal-25.webp"})

    def test_rejects_unknown_buildings_and_invalid_stages(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)
            (source / "unknown-standard-01.png").write_bytes(b"test")
            (source / "hq-standard-26.png").write_bytes(b"test")
            _, errors = candidates(source)
            self.assertEqual(len(errors), 2)

    def test_prevents_two_inputs_targeting_same_level(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)
            (source / "hq-standard-03.png").write_bytes(b"test")
            (source / "hq-standard-03.webp").write_bytes(b"test")
            _, errors = candidates(source)
            self.assertTrue(any("same stage" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
