from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.check_repository import MAX_SCANNED_FILE_BYTES, audit_file


class AuditFileTests(unittest.TestCase):
    def test_rejects_symbolic_links(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "target.txt").write_text("contenido", encoding="utf-8")
            (root / "link.txt").symlink_to(root / "target.txt")

            self.assertEqual(
                audit_file("link.txt", root),
                ["enlace simbólico no permitido: link.txt"],
            )

    def test_rejects_files_above_scan_limit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with (root / "large.txt").open("wb") as file:
                file.truncate(MAX_SCANNED_FILE_BYTES + 1)

            failures = audit_file("large.txt", root)

            self.assertEqual(len(failures), 1)
            self.assertIn("archivo demasiado grande para auditar", failures[0])

    def test_skips_content_checks_for_already_forbidden_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "private.zip").symlink_to(root / "missing-target")

            self.assertEqual(
                audit_file("private.zip", root),
                ["formato privado o binario versionado: private.zip"],
            )


if __name__ == "__main__":
    unittest.main()
