from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import unittest
from pathlib import Path

from integration import test_context_cli as context_support


SKILL_ROOT = context_support.SKILL_ROOT
GOLDEN_FIXTURE = SKILL_ROOT / "tests" / "fixtures" / "golden-v1" / "valid.json"


class GoldenCliIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = context_support.ContextCliIntegrationTests(
            methodName="test_context_queries_project_first_and_normalizes_hits"
        )
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        (self.fixture.repo / ".agents" / "memory").mkdir()
        shutil.copyfile(
            GOLDEN_FIXTURE,
            self.fixture.repo / ".agents" / "memory" / "golden.json",
        )
        (self.fixture.vault / "wiki" / "index.md").write_text(
            "# Index\n\n"
            "- [[entities/project|Project]]\n"
            "- [[entities/skillz-claude|Skillz-Claude]]\n"
            "- [[concepts/project-memory-workflow|Project Memory Workflow]]\n",
            encoding="utf-8",
        )

    def test_memory_test_runs_eight_paired_cases_and_persists_metadata_only(self) -> None:
        golden_text = GOLDEN_FIXTURE.read_text(encoding="utf-8")
        queries = [case["query"] for case in json.loads(golden_text)["cases"]]

        result = self.fixture._run_memory_cli("test", "--json")
        output = json.loads(result.stdout)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output["command"], "test")
        self.assertEqual(output["status"], "ready")
        self.assertRegex(output["run_id"], r"^run_\d{8}T\d{12}Z_[0-9a-f]{16}$")
        self.assertEqual(len(output["data"]["cases"]), 8)
        self.assertEqual(output["data"]["estimator_version"], "utf8_bytes_div_4_v1")
        self.assertGreater(output["data"]["aggregate"]["retrieval_hit_rate"], 0)
        self.assertEqual(output["data"]["aggregate"]["fallback_rate"], 0)

        run_files = list((self.fixture.state_dir / "runs" / "skillz-claude").glob("*.json"))
        self.assertEqual(len(run_files), 1)
        persisted = run_files[0].read_text(encoding="utf-8")
        serialized = result.stdout + result.stderr + persisted
        for query in queries:
            self.assertNotIn(query, serialized)
        self.assertFalse(list(self.fixture.state_dir.rglob("*.jsonl")))
        self.assertNotIn(str(self.fixture.repo), persisted)
        self.assertNotIn("content", persisted)
        self.assertNotIn("snippet", persisted)
        invocations = [
            json.loads(line)
            for line in self.fixture.qmd_log.read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(len(invocations), 8)
        self.assertEqual(
            {invocation["query_sha256"] for invocation in invocations},
            {
                hashlib.sha256(query.encode("utf-8")).hexdigest()
                for query in queries
            },
        )
        if os.name == "posix":
            self.assertEqual(stat.S_IMODE(run_files[0].stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(run_files[0].parent.stat().st_mode), 0o700)

    def test_invalid_suite_blocks_before_qmd_or_state_mutation(self) -> None:
        path = self.fixture.repo / ".agents" / "memory" / "golden.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["cases"] = payload["cases"][:7]
        path.write_text(json.dumps(payload), encoding="utf-8")

        result = self.fixture._run_memory_cli("test", "--json")
        output = json.loads(result.stdout)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output["status"], "blocked")
        self.assertEqual(output["errors"][0]["code"], "golden_case_count_invalid")
        self.assertEqual(self.fixture.qmd_log.read_text(encoding="utf-8"), "")
        self.assertFalse(self.fixture.state_dir.exists())

    def test_missing_baseline_page_blocks_every_comparison_before_qmd(self) -> None:
        (self.fixture.vault / "wiki" / "entities" / "project.md").unlink()

        result = self.fixture._run_memory_cli("test", "--json")
        output = json.loads(result.stdout)

        self.assertEqual(result.returncode, 32)
        self.assertEqual(output["errors"][0]["code"], "golden_baseline_unavailable")
        self.assertEqual(self.fixture.qmd_log.read_text(encoding="utf-8"), "")
        self.assertFalse(self.fixture.state_dir.exists())

    def test_human_output_exposes_the_same_functional_aggregate_without_queries(self) -> None:
        result = self.fixture._run_memory_cli(
            "test",
            extra_env={"NO_COLOR": "1"},
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Memory test ready", result.stdout)
        self.assertIn("Cases: 8", result.stdout)
        self.assertIn("Retrieval hit rate:", result.stdout)
        self.assertIn("Fallback rate:", result.stdout)
        self.assertIn("Median context reduction:", result.stdout)
        self.assertNotIn("How is the memory runtime installed?", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
