from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class ReleaseCandidateDocumentationTests(unittest.TestCase):
    def test_readme_uses_neutral_core_and_marks_rc_non_stable(self):
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("core/catalog.yaml", readme)
        self.assertIn("6.1.0-rc.1", readme)
        self.assertIn("not stable", readme)
        self.assertNotIn("Claude is the source of truth", readme)
        self.assertNotIn("mirror `.claude/` as the single source of truth", readme)

    def test_compatibility_matrix_names_every_generated_provider_and_levels(self):
        matrix = (REPO_ROOT / "docs/compatibility/matrix-v6.1.md").read_text(encoding="utf-8")
        for provider in ("Claude", "Codex", "OpenCode", "Generic", "Gemini", "Grok", "Kimi"):
            self.assertIn(provider, matrix)
        for level in ("C1", "C2", "C3"):
            self.assertIn(level, matrix)
        self.assertIn("Kimi model via Codex/OpenCodex", matrix)
        self.assertIn("Flat `prompts/*.md` are diagnostic/legacy fallbacks", matrix)

    def test_release_candidate_is_machine_readable_and_not_stable(self):
        report = json.loads(
            (REPO_ROOT / "docs/compatibility/release-candidate-v6.1.0-rc.1.json").read_text()
        )
        self.assertEqual(report["release"], "6.1.0-rc.1")
        self.assertFalse(report["stable"])
        self.assertEqual(report["real_usage_bake"]["status"], "not-started")
        self.assertGreaterEqual(len(report["stable_blockers"]), 7)
        self.assertEqual(report["runtime_routes"]["codex"]["certification"], "C2")
        self.assertNotEqual(report["runtime_routes"]["claude"]["certification"], "C3")

    def test_catalog_and_changelog_use_the_rc_version(self):
        catalog = json.loads((REPO_ROOT / "core/catalog.yaml").read_text(encoding="utf-8"))
        changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertEqual(catalog["distribution"]["version"], "6.1.0-rc.1")
        self.assertIn("## [6.1.0-rc.1] - 2026-09-02", changelog)


if __name__ == "__main__":
    unittest.main()
