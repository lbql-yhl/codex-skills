from __future__ import annotations

import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "github-project-memory" / "scripts" / "github_project_memory.py"

spec = importlib.util.spec_from_file_location("github_project_memory", SCRIPT)
assert spec and spec.loader
memory_tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(memory_tool)


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

    def test_github_project_memory_is_registered(self):
        item = next(item for item in self.manifest["skills"] if item["name"] == "github-project-memory")
        self.assertEqual(item["path"], "skills/github-project-memory")
        self.assertTrue((ROOT / item["path"] / "scripts" / "github_project_memory.py").is_file())
        schema = (ROOT / item["path"] / "references" / "memory-schema.md").read_text(encoding="utf-8")
        self.assertIn('"repositories"', schema)
        self.assertIn('"skills"', schema)

    def test_github_helpers_are_local_and_safe(self):
        self.assertEqual(memory_tool.parse_owner("lbql-yhl"), "lbql-yhl")
        self.assertEqual(memory_tool.parse_owner("https://github.com/lbql-yhl/"), "lbql-yhl")
        name, description = memory_tool.parse_skill_frontmatter(
            "---\nname: demo-skill\ndescription: A demo skill.\n---\n# Demo\n", "fallback"
        )
        self.assertEqual((name, description), ("demo-skill", "A demo skill."))
        with self.assertRaises(ValueError):
            memory_tool.parse_owner("https://example.com/not-github")

    def test_memory_query_does_not_need_network(self):
        memory = {
            "repositories": [
                {
                    "full_name": "lbql-yhl/demo",
                    "description": "A demo project",
                    "html_url": "https://github.com/lbql-yhl/demo",
                    "skills": [
                        {
                            "name": "demo-skill",
                            "description": "Reusable workflow",
                            "path": "skills/demo-skill/SKILL.md",
                            "references": [],
                            "scripts": [],
                        }
                    ],
                }
            ]
        }
        matches = memory_tool.find_matches(memory, "workflow")
        self.assertEqual(len(matches["skills"]), 1)
        self.assertEqual(matches["skills"][0]["repository"], "lbql-yhl/demo")

    def test_no_private_runtime_artifacts(self):
        forbidden = {".env", ".venv", "node_modules", "recruitment.sqlite3"}
        found = [p for p in ROOT.rglob("*") if p.name in forbidden]
        self.assertEqual([], found)


if __name__ == "__main__":
    unittest.main()
