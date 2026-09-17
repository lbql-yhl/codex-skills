import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RepositoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8-sig"))

    def test_manifest_skill_paths_exist(self):
        names = set()
        for item in self.manifest["skills"]:
            self.assertNotIn(item["name"], names)
            names.add(item["name"])
            path = ROOT / item["path"]
            self.assertTrue(path.is_dir(), item["name"])
            skill_file = path / "SKILL.md"
            self.assertTrue(skill_file.is_file(), item["name"])
            text = skill_file.read_text(encoding="utf-8-sig")
            self.assertRegex(text, r"(?m)^---\s*$")
            self.assertRegex(text, r"(?m)^name:\s*[a-z0-9-]+\s*$")
            self.assertRegex(text, r"(?m)^description:\s*.+$")

    def test_skill_names_match_manifest(self):
        for item in self.manifest["skills"]:
            text = (ROOT / item["path"] / "SKILL.md").read_text(encoding="utf-8-sig")
            match = re.search(r"(?m)^name:\s*([^\r\n]+)", text)
            self.assertIsNotNone(match, item["name"])
            self.assertEqual(item["name"], match.group(1).strip())

    def test_no_private_runtime_artifacts(self):
        forbidden = {".env", ".venv", "node_modules", "recruitment.sqlite3"}
        found = [p for p in ROOT.rglob("*") if p.name in forbidden]
        self.assertEqual([], found)


if __name__ == "__main__":
    unittest.main()
