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
            "---\nname: demo\ndescription: Demo\nmodel: opus\nallowed-tools:\n  - Read\n---\n"
            "Read .claude/skills/demo/SKILL.md and .claude/skills/demo/references/x.md.\n"
            "Then use .claude/knowledge/testing/x.md, ../../knowledge/testing/y.md, "
            "and ~/.claude/skills/demo/SKILL.md.\n"
        )
        normalized = MIGRATION._normalize_entry(source, "skill", "demo")
        self.assertIn("skill:demo", normalized)
        self.assertIn("skill:demo/references/x.md", normalized)
        self.assertIn("references/knowledge/testing/x.md", normalized)
        self.assertIn("references/knowledge/testing/y.md", normalized)
        self.assertIn("~/.claude/skills/demo/SKILL.md", normalized)
        self.assertNotIn("model: opus", normalized)
        self.assertEqual(
            MIGRATION._provider_frontmatter(source, "skill", "demo"),
            "model: opus\nallowed-tools:\n  - Read\n",
        )

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

    def test_knowledge_path_traversal_is_rejected(self):
        with self.assertRaisesRegex(MIGRATION.MigrationError, "unsafe knowledge resource path"):
            MIGRATION._safe_knowledge_path("../../secret.md")

    def test_apply_refuses_to_overwrite_canonical_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            legacy = root / ".claude" / "skills" / "demo" / "SKILL.md"
            legacy.parent.mkdir(parents=True)
            legacy.write_text("# Legacy\n", encoding="utf-8")
            (root / ".claude" / "commands").mkdir(parents=True)
            canonical = root / "core" / "skills" / "demo" / "SKILL.md"
            canonical.parent.mkdir(parents=True)
            canonical.write_text("# Canonical edit\n", encoding="utf-8")
            with self.assertRaisesRegex(MIGRATION.MigrationError, "canonical entry drift"):
                MIGRATION._copy_artifacts(root)

    def test_explicit_frontmatter_extraction_only_accepts_pre_extraction_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            legacy = root / ".claude" / "skills" / "demo" / "SKILL.md"
            legacy.parent.mkdir(parents=True)
            legacy.write_text(
                "---\nname: demo\ndescription: Demo\nmodel: opus\n---\n# Demo\n",
                encoding="utf-8",
            )
            (root / ".claude" / "commands").mkdir(parents=True)
            canonical = root / "core" / "skills" / "demo" / "SKILL.md"
            canonical.parent.mkdir(parents=True)
            canonical.write_text(legacy.read_text(encoding="utf-8"), encoding="utf-8")
            MIGRATION._copy_artifacts(root, extract_provider_metadata=True)
            self.assertNotIn("model: opus", canonical.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
