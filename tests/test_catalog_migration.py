from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "tooling" / "migration" / "migrate_catalog.py"
SPEC = importlib.util.spec_from_file_location("migrate_catalog", MODULE_PATH)
assert SPEC and SPEC.loader
MIGRATION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MIGRATION)


class CatalogMigrationTests(unittest.TestCase):
    def test_repository_catalog_covers_every_legacy_skill_command_and_resource(self):
        catalog = json.loads((REPO_ROOT / "core" / "catalog.yaml").read_text(encoding="utf-8"))
        self.assertEqual(MIGRATION._check(REPO_ROOT, catalog), [])

    def test_catalog_migration_report_is_fresh(self):
        result = subprocess.run(
            [
                "bash",
                "tests/run-python310.sh",
                "tooling/migration/migrate_catalog.py",
                "--root",
                ".",
                "--report",
                "docs/compatibility/catalog-migration-v6.1.json",
            ],
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_normalization_preserves_user_home_paths(self):
        source = (
            "Read .claude/skills/demo/SKILL.md and .claude/skills/demo/references/x.md.\n"
            "Then use .claude/knowledge/testing/x.md and ~/.claude/skills/demo/SKILL.md.\n"
        )
        normalized = MIGRATION._normalize_entry(source, "skill", "demo")
        self.assertIn("skill:demo", normalized)
        self.assertIn("skill:demo/references/x.md", normalized)
        self.assertIn("references/knowledge/testing/x.md", normalized)
        self.assertIn("~/.claude/skills/demo/SKILL.md", normalized)

    def test_command_knowledge_resources_are_namespaced(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "core" / "commands" / "review.md"
            source.parent.mkdir(parents=True)
            source.write_text("Use resources/review/knowledge/testing/x.md\n", encoding="utf-8")
            knowledge = root / ".claude" / "knowledge" / "testing" / "x.md"
            knowledge.parent.mkdir(parents=True)
            knowledge.write_text("proof\n", encoding="utf-8")
            canonical_knowledge = root / "core" / "knowledge" / "testing" / "x.md"
            canonical_knowledge.parent.mkdir(parents=True)
            canonical_knowledge.write_text("proof\n", encoding="utf-8")
            legacy = root / ".claude" / "commands" / "review.md"
            legacy.parent.mkdir(parents=True)
            legacy.write_text("Use .claude/knowledge/testing/x.md\n", encoding="utf-8")
            resources = MIGRATION._resource_items(root, "command", "review", source)
            self.assertEqual(resources, [{
                "source": "core/knowledge/testing/x.md",
                "output": "resources/review/knowledge/testing/x.md",
            }])


if __name__ == "__main__":
    unittest.main()
