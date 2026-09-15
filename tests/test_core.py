import json
import tempfile
import unittest
from pathlib import Path
from evidence_manifest.core import (
    create_manifest,
    load_manifest,
    verify_manifest,
    write_manifest,
)
class ManifestTests(unittest.TestCase):
    def test_create_and_verify_relative_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "a.txt").write_text("alpha", encoding="utf-8")
            (root / "nested").mkdir()
            (root / "nested" / "b.txt").write_text("beta", encoding="utf-8")
            output = root / "manifest.json"
            manifest = create_manifest(root, output_path=output)
            write_manifest(manifest, output)
            self.assertEqual(manifest["file_count"], 2)
            self.assertTrue(verify_manifest(root, output)["ok"])
            self.assertEqual(load_manifest(output)["format_version"], 1)
    def test_tampering_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            file_path = root / "record.txt"
            file_path.write_text("before", encoding="utf-8")
            output = root / "manifest.json"
            write_manifest(create_manifest(root, output_path=output), output)
            file_path.write_text("after", encoding="utf-8")
            result = verify_manifest(root, output)
            self.assertFalse(result["ok"])
            self.assertEqual(result["modified"], ["record.txt"])
    def test_hashed_mode_does_not_store_filename(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sensitive_name = "private-name.txt"
            (root / sensitive_name).write_text("synthetic", encoding="utf-8")
            output = root / "manifest.json"
            write_manifest(
                create_manifest(root, output_path=output, path_mode="hashed"), output
            )
            serialized = output.read_text(encoding="utf-8")
            self.assertNotIn(sensitive_name, serialized)
            self.assertTrue(verify_manifest(root, output)["ok"])
    def test_duplicate_content_is_grouped(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "first.bin").write_bytes(b"same")
            (root / "second.bin").write_bytes(b"same")
            manifest = create_manifest(root)
            self.assertEqual(len(manifest["duplicate_groups"]), 1)
            self.assertEqual(
                manifest["duplicate_groups"][0]["files"],
                ["first.bin", "second.bin"],
            )
    def test_manifest_is_valid_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "manifest.json"
            write_manifest(create_manifest(root, output_path=output), output)
            json.loads(output.read_text(encoding="utf-8"))
if __name__ == "__main__":
    unittest.main()
