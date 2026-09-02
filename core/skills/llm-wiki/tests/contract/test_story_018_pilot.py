from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(SKILL_ROOT))

from memory_cli.golden import load_golden_suite  # noqa: E402
from memory_cli.manifest import load_manifest  # noqa: E402
from memory_cli.quality import load_quality_rubric  # noqa: E402


MANIFEST_PATH = REPO_ROOT / ".agents" / "memory.yaml"
GOLDEN_PATH = REPO_ROOT / ".agents" / "memory" / "golden.json"
RUBRIC_PATH = REPO_ROOT / ".agents" / "memory" / "quality-rubric.json"

EXPECTED_ENTRY_PAGES = (
    "wiki/entities/skillz-claude.md",
    "wiki/concepts/project-memory-workflow.md",
    "wiki/concepts/local-rag-stack.md",
)

EXPECTED_GOLDEN_CASES = {
    "install-provider-runtime",
    "depct-development-workflow",
    "proven-quality-gate",
    "llm-wiki-task-first",
    "qmd-local-retrieval",
    "project-memory-precedence",
    "multi-runtime-source-of-truth",
    "memory-freshness-boundary",
}

LOCAL_ONLY_PATHS = (
    ".agents/memory.local.json",
    ".agents/memory/holdout.local.json",
    ".agents/project-memory.md",
    ".claude/project-memory.md",
)


class SkillzClaudePilotContractTests(unittest.TestCase):
    def test_manifest_activates_one_project_store_without_fallback(self) -> None:
        manifest = load_manifest(MANIFEST_PATH)

        self.assertEqual(manifest.project.id, "skillz-claude")
        self.assertEqual(manifest.stores.project.collection, "elsolal-wiki")
        self.assertEqual(
            tuple(path.as_posix() for path in manifest.stores.project.entry_pages),
            EXPECTED_ENTRY_PAGES,
        )
        self.assertEqual(manifest.fallbacks, ())
        self.assertFalse(manifest.policy.full_index_fallback)
        self.assertEqual(manifest.golden.visible_path.as_posix(), ".agents/memory/golden.json")
        self.assertEqual(
            manifest.golden.quality_rubric.as_posix(),
            ".agents/memory/quality-rubric.json",
        )

    def test_visible_suite_has_the_eight_approved_pilot_topics(self) -> None:
        suite = load_golden_suite(GOLDEN_PATH)

        self.assertEqual({case.case_id for case in suite.cases}, EXPECTED_GOLDEN_CASES)
        self.assertTrue(any(case.expected_sources for case in suite.cases))
        self.assertTrue(
            all(3 <= len(case.baseline_pages) <= 10 for case in suite.cases)
        )

    def test_quality_rubric_is_the_closed_quality_v1_contract(self) -> None:
        rubric = load_quality_rubric(RUBRIC_PATH)

        self.assertEqual(rubric.rubric_version, "quality-v1")
        self.assertEqual(rubric.minimum_score, 0)
        self.assertEqual(rubric.maximum_score, 100)
        self.assertAlmostEqual(sum(item.weight for item in rubric.dimensions), 1.0)

    def test_private_projection_holdout_and_pointers_are_never_tracked(self) -> None:
        for relative_path in LOCAL_ONLY_PATHS:
            with self.subTest(path=relative_path):
                result = subprocess.run(
                    ["git", "ls-files", "--error-unmatch", relative_path],
                    cwd=REPO_ROOT,
                    check=False,
                    text=True,
                    capture_output=True,
                )
                self.assertNotEqual(result.returncode, 0)

    def test_agent_documentation_explains_the_local_pilot_boundary(self) -> None:
        documentation = (REPO_ROOT / ".agents" / "README.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Pilote memory Skillz-Claude", documentation)
        self.assertIn("sans fallback", documentation)
        self.assertIn("degraded", documentation)
        self.assertIn("holdout.local.json", documentation)


if __name__ == "__main__":
    unittest.main()
