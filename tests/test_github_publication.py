from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class GitHubPublicationTests(unittest.TestCase):
    def read(self, name: str) -> str:
        return (ROOT / name).read_text(encoding="utf-8")

    def test_code_license_is_noncommercial(self):
        text = self.read("LICENSE")
        self.assertIn("PolyForm Noncommercial License 1.0.0", text)
        self.assertIn("Required Notice: Copyright (c) 2026 Sławomir Ramian", text)
        self.assertIn("Any noncommercial purpose is a permitted purpose.", text)

    def test_document_license_preserves_zenodo_boundary(self):
        text = self.read("LICENSE-DOCUMENTATION.md")
        self.assertIn("CC BY 4.0", text)
        self.assertIn("CC BY-NC 4.0", text)
        self.assertRegex(text, r"nie\s+odwołuje ani nie ogranicza praw")

    def test_citation_uses_code_license_identifier(self):
        text = self.read("CITATION.cff")
        self.assertIn("license: PolyForm-Noncommercial-1.0.0", text)
        self.assertNotIn("license: MIT", text)

    def test_commercial_permission_is_explicit(self):
        text = self.read("COMMERCIAL-LICENSE.md")
        self.assertIn("uprzedniej pisemnej zgody", text)
        self.assertIn("Sławomir Ramian", text)

    def test_red_is_reserved_for_errors(self):
        text = self.read("PREPARE_GITHUB_PUBLICATION.ps1")
        for line in text.splitlines():
            if "ForegroundColor Red" in line:
                self.assertTrue("ERROR" in line or "BŁĄD" in line)


if __name__ == "__main__":
    unittest.main()
