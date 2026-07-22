from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT))

from memory_cli.context import run_context  # noqa: E402
from memory_cli.contracts import RetrievalMode, TaskCategory  # noqa: E402


SEARCH_FIXTURE = SKILL_ROOT / "tests" / "fixtures" / "qmd-0.9" / "search-results.json"


class ContextCliIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.repo = self.root / "repo"
        self.vault = self.root / "vault"
        self.shared_vault = self.root / "shared-vault"
        (self.repo / ".agents").mkdir(parents=True)
        (self.vault / "wiki" / "entities").mkdir(parents=True)
        (self.vault / "wiki" / "concepts").mkdir(parents=True)
        (self.shared_vault / "wiki" / "sources").mkdir(parents=True)
        (self.vault / "wiki" / "entities" / "project.md").write_text("# Project\n")
        (self.vault / "wiki" / "entities" / "skillz-claude.md").write_text(
            "---\ntitle: Skillz-Claude\ncategory: entity\n---\n"
            "# Skillz-Claude\n\nProject overview.\n\nAgent tooling.\n\n"
            "Portable workflows.\n\nRepo d'outillage multi-runtime.\n",
            encoding="utf-8",
        )
        (self.vault / "wiki" / "concepts" / "project-memory-workflow.md").write_text(
            "# Project Memory Workflow\n\n"
            "Activation.\n\nProjection.\n\nRetrieval.\n\nSufficiency.\n\n"
            "Budgets.\n\nReceipts.\n\nFreshness.\n\nConflicts.\n\n"
            "Le codebase reste la source de vérité immédiate.\n",
            encoding="utf-8",
        )
        (self.shared_vault / "wiki" / "entities").mkdir(parents=True)
        (self.shared_vault / "wiki" / "concepts").mkdir(parents=True)
        (self.shared_vault / "wiki" / "entities" / "skillz-claude.md").write_text(
            (self.vault / "wiki" / "entities" / "skillz-claude.md").read_text(),
            encoding="utf-8",
        )
        (self.shared_vault / "wiki" / "concepts" / "project-memory-workflow.md").write_text(
            (self.vault / "wiki" / "concepts" / "project-memory-workflow.md").read_text(),
            encoding="utf-8",
        )
        (self.shared_vault / "wiki" / "sources" / "shared.md").write_text(
            "# Shared source\n\nShared context.\n",
            encoding="utf-8",
        )
        (self.vault / "wiki" / "entities" / "oversized.md").write_text(
            "# Oversized evidence\n\n" + ("critical-data-" * 2400) + "\n",
            encoding="utf-8",
        )
        self._write_activation()
        subprocess.run(["git", "init", "-b", "main"], cwd=self.repo, check=True, capture_output=True)
        self.qmd_log = self.root / "qmd-invocations.jsonl"
        self.qmd_log.write_text("")
        self.qmd = self._make_qmd()

    def _write_activation(
        self,
        *,
        role: str = "owner",
        include_fallback_store: bool = True,
    ) -> None:
        manifest = {
            "schema_version": 1,
            "project": {"id": "skillz-claude", "name": "Skillz-Claude", "owner": "Tests"},
            "stores": {
                "project": {
                    "remote": "https://example.test/memory.git",
                    "collection": "elsolal-wiki",
                    "entry_pages": ["wiki/entities/project.md"],
                }
            },
            "fallbacks": [
                {
                    "id": "transverse",
                    "collection": "shared-wiki",
                    "allowed_roles": ["owner"],
                    "task_categories": ["architecture", "historical"],
                    "entry_pages": ["wiki/sources/shared.md"],
                }
            ],
            "budgets": {
                "minimal": {"target_tokens": 800, "hard_tokens": 1200},
                "project": {"target_tokens": 2500, "hard_tokens": 4000},
                "historical": {"target_tokens": 6000, "hard_tokens": 9000},
            },
            "policy": {
                "semantic_retrieval": "explicit",
                "full_index_fallback": True,
                "retention_days": 30,
                "sufficiency_thresholds_version": "qmd-0.9-v1",
            },
            "golden": {
                "visible_path": ".agents/memory/golden.json",
                "quality_rubric": ".agents/memory/quality-rubric.json",
            },
        }
        stores = {"project": {"root": str(self.vault)}}
        if include_fallback_store:
            stores["transverse"] = {"root": str(self.shared_vault)}
        projection = {
            "schema_version": 1,
            "principal": {"role": role},
            "stores": stores,
        }
        (self.repo / ".agents" / "memory.yaml").write_text(json.dumps(manifest))
        (self.repo / ".agents" / "memory.local.json").write_text(json.dumps(projection))

    def _make_qmd(self) -> Path:
        binary = self.root / "qmd-fixture"
        binary.write_text(
            "#!/usr/bin/env python3\n"
            "import hashlib, json, os, sys\n"
            f"fixture = {str(SEARCH_FIXTURE)!r}\n"
            f"log = {str(self.qmd_log)!r}\n"
            "command = sys.argv[1] if len(sys.argv) > 1 else ''\n"
            "freshness = os.environ.get('FAKE_QMD_FRESHNESS', 'fresh')\n"
            "if command == '--version': print('qmd 0.9.0'); raise SystemExit\n"
            "if command == 'status':\n"
            "    age = '3d ago' if freshness == 'stale' else '3h ago'\n"
            "    print('Collections')\n"
            "    if freshness != 'project-unknown':\n"
            "        print('  elsolal-wiki (qmd://elsolal-wiki/)')\n"
            "        print(f'    Files: 179 (updated {age})')\n"
            "    print('  shared-wiki (qmd://shared-wiki/)')\n"
            "    print('    Files: 12 (updated 2h ago)')\n"
            "    raise SystemExit\n"
            "query = sys.argv[2] if len(sys.argv) > 2 else ''\n"
            "collection = sys.argv[sys.argv.index('-c') + 1] if '-c' in sys.argv else None\n"
            "min_score = sys.argv[sys.argv.index('--min-score') + 1] if '--min-score' in sys.argv else None\n"
            "with open(log, 'a', encoding='utf-8') as stream:\n"
            "    stream.write(json.dumps({'command': command, 'collection': collection, "
            "'min_score': min_score, "
            "'query_sha256': hashlib.sha256(query.encode()).hexdigest()}) + '\\n')\n"
            "mode = os.environ.get('FAKE_QMD_MODE', 'ready')\n"
            "if mode == 'empty': print('[]')\n"
            "elif mode == 'invalid': print('{not-json')\n"
            "elif mode in {'fallback', 'fallback-empty'} and collection == 'elsolal-wiki':\n"
            "    print(json.dumps([{'docid': '#600000', 'score': 0.60, "
            "'file': 'qmd://elsolal-wiki/entities/project.md', 'title': 'Project', "
            "'snippet': '@@ -1,2 @@\\n\\nProject context.'}]))\n"
            "elif mode == 'fallback' and collection == 'shared-wiki':\n"
            "    print(json.dumps([{'docid': '#900000', 'score': 0.90, "
            "'file': 'qmd://shared-wiki/sources/shared.md', 'title': 'Shared source', "
            "'snippet': '@@ -1,2 @@\\n\\nShared context.'}]))\n"
            "elif mode == 'fallback-empty' and collection == 'shared-wiki': print('[]')\n"
            "elif mode == 'oversized':\n"
            "    print(json.dumps([{'docid': '#777777', 'score': 0.91, "
            "'file': f'qmd://{collection}/entities/oversized.md', 'title': 'Oversized', "
            "'snippet': '@@ -3,1 @@\\n\\ncritical-data-'}]))\n"
            "else:\n"
            "    with open(fixture, encoding='utf-8') as stream:\n"
            "        print(stream.read().replace('qmd://elsolal-wiki/', f'qmd://{collection}/'))\n"
        )
        binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
        return binary

    def _run_cli(
        self,
        *arguments: str,
        stdin: str | None = None,
        fake_mode: str = "ready",
        freshness: str = "fresh",
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment.update(
            {
                "PYTHONPATH": str(SKILL_ROOT),
                "SKILLZ_MEMORY_QMD": str(self.qmd),
                "FAKE_QMD_MODE": fake_mode,
                "FAKE_QMD_FRESHNESS": freshness,
            }
        )
        return subprocess.run(
            [sys.executable, "-m", "memory_cli", "context", *arguments],
            cwd=self.repo,
            env=environment,
            input=stdin,
            check=False,
            text=True,
            capture_output=True,
        )

    def test_context_queries_project_first_and_normalizes_hits(self) -> None:
        result = self._run_cli(
            "--mode",
            "project",
            "--task-category",
            "architecture",
            "--json",
            "agentic coding",
        )
        output = json.loads(result.stdout)
        invocation = json.loads(self.qmd_log.read_text().splitlines()[0])

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output["status"], "sufficient")
        self.assertEqual(output["data"]["route"], ["elsolal-wiki"])
        self.assertEqual(output["data"]["retrieval"]["status"], "ready")
        self.assertEqual(output["data"]["decision"]["status"], "sufficient")
        self.assertEqual(output["data"]["decision"]["reason_codes"], [])
        self.assertEqual(output["data"]["retrieval"]["hits"][0]["path"], "entities/skillz-claude.md")
        self.assertNotIn("agentic coding", result.stdout)
        self.assertIsInstance(output["data"]["retrieval"]["duration_ms"], int)
        self.assertEqual(invocation["command"], "search")
        self.assertEqual(invocation["collection"], "elsolal-wiki")
        self.assertEqual(len(self.qmd_log.read_text().splitlines()), 1)
        self.assertEqual(output["data"]["context"]["status"], "ready")
        self.assertEqual(output["data"]["context"]["retrieved_count"], 2)
        self.assertEqual(output["data"]["context"]["read_count"], 1)
        self.assertEqual(output["data"]["context"]["budget"]["target_tokens"], 2500)
        self.assertEqual(output["data"]["context"]["budget"]["hard_tokens"], 4000)
        self.assertEqual(
            output["data"]["context"]["estimator_version"],
            "utf8_bytes_div_4_v1",
        )
        self.assertIn("Repo d'outillage", output["data"]["context"]["sections"][0]["content"])

    def test_authorized_fallback_runs_after_project_insufficiency_with_reason_codes(self) -> None:
        result = self._run_cli(
            "--mode",
            "project",
            "--task-category",
            "architecture",
            "--json",
            "cross-project decision",
            fake_mode="fallback",
        )
        output = json.loads(result.stdout)
        invocations = [json.loads(line) for line in self.qmd_log.read_text().splitlines()]

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output["status"], "sufficient")
        self.assertEqual(output["data"]["route"], ["elsolal-wiki", "shared-wiki"])
        self.assertTrue(output["data"]["fallback"]["used"])
        self.assertIn(
            "insufficient_coverage",
            output["data"]["fallback"]["reason_codes"],
        )
        self.assertEqual(
            [invocation["collection"] for invocation in invocations],
            ["elsolal-wiki", "shared-wiki"],
        )
        self.assertEqual([invocation["min_score"] for invocation in invocations], ["0.55", "0.55"])

    def test_empty_fallback_keeps_aggregate_retrieval_status_consistent_with_project_hits(self) -> None:
        result = self._run_cli(
            "--mode",
            "project",
            "--task-category",
            "architecture",
            "--json",
            "cross-project decision",
            fake_mode="fallback-empty",
        )
        output = json.loads(result.stdout)

        self.assertEqual(result.returncode, 20, result.stderr)
        self.assertEqual(output["status"], "insufficient")
        self.assertEqual(output["data"]["retrieval"]["status"], "ready")
        self.assertEqual(len(output["data"]["retrieval"]["hits"]), 1)
        self.assertEqual(output["data"]["decision"]["reason_codes"], ["no_result"])

    def test_policy_denial_never_calls_or_reveals_transverse_collection(self) -> None:
        denied_cases = (
            ("collaborator", "architecture"),
            ("owner", "general"),
        )

        for role, task_category in denied_cases:
            with self.subTest(role=role, task_category=task_category):
                self._write_activation(role=role)
                self.qmd_log.write_text("")

                result = self._run_cli(
                    "--mode",
                    "project",
                    "--task-category",
                    task_category,
                    "--json",
                    "cross-project decision",
                    fake_mode="fallback",
                )
                output = json.loads(result.stdout)
                invocations = [json.loads(line) for line in self.qmd_log.read_text().splitlines()]

                self.assertEqual(result.returncode, 20, result.stderr)
                self.assertEqual(output["status"], "insufficient")
                self.assertEqual(output["data"]["route"], ["elsolal-wiki"])
                self.assertEqual(output["warnings"][0]["code"], "fallback_not_authorized")
                self.assertEqual(len(invocations), 1)
                self.assertNotIn("shared-wiki", result.stdout)

    def test_ambiguous_context_waits_for_explicit_fallback_decision(self) -> None:
        stopped = self._run_cli(
            "--mode",
            "project",
            "--task-category",
            "architecture",
            "--json",
            "ambiguous freshness",
            freshness="project-unknown",
        )
        stopped_output = json.loads(stopped.stdout)

        self.assertEqual(stopped.returncode, 21, stopped.stderr)
        self.assertEqual(stopped_output["status"], "ambiguous")
        self.assertEqual(len(self.qmd_log.read_text().splitlines()), 1)

        self.qmd_log.write_text("")
        continued = self._run_cli(
            "--mode",
            "project",
            "--task-category",
            "architecture",
            "--fallback-on-ambiguous",
            "--json",
            "ambiguous freshness",
            freshness="project-unknown",
        )
        continued_output = json.loads(continued.stdout)

        self.assertEqual(continued.returncode, 0, continued.stderr)
        self.assertEqual(continued_output["status"], "sufficient")
        self.assertTrue(continued_output["data"]["fallback"]["explicit_decision"])
        self.assertEqual(len(self.qmd_log.read_text().splitlines()), 2)

    def test_explain_human_output_contains_the_same_reason_codes(self) -> None:
        result = self._run_cli(
            "--mode",
            "project",
            "--task-category",
            "architecture",
            "--explain",
            "cross-project decision",
            fake_mode="fallback",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Reason codes", result.stdout)
        self.assertIn("insufficient_coverage", result.stdout)

    def test_hard_cap_requires_an_explicit_risk_reason_in_cli_output(self) -> None:
        stopped = self._run_cli(
            "--mode",
            "project",
            "--task-category",
            "security",
            "--json",
            "oversized evidence",
            fake_mode="oversized",
        )
        stopped_output = json.loads(stopped.stdout)

        allowed = self._run_cli(
            "--mode",
            "project",
            "--task-category",
            "security",
            "--risk-reason",
            "security",
            "--json",
            "oversized evidence",
            fake_mode="oversized",
        )
        allowed_output = json.loads(allowed.stdout)

        self.assertEqual(stopped.returncode, 20, stopped.stderr)
        self.assertEqual(stopped_output["status"], "insufficient")
        self.assertEqual(stopped_output["data"]["context"]["status"], "partial")
        self.assertIn(
            "hard_cap_reached",
            stopped_output["data"]["context"]["reason_codes"],
        )
        self.assertEqual(allowed.returncode, 0, allowed.stderr)
        self.assertEqual(allowed_output["status"], "sufficient")
        self.assertTrue(allowed_output["data"]["context"]["hard_cap_exceeded"])
        self.assertEqual(allowed_output["data"]["context"]["risk_reason"], "security")
        self.assertGreater(
            allowed_output["data"]["context"]["estimated_tokens"],
            allowed_output["data"]["context"]["budget"]["hard_tokens"],
        )

    def test_query_stdin_is_not_persisted_or_rendered_and_cannot_inject_shell(self) -> None:
        escaped = self.root / "shell-injection"
        query = f"private-sentinel-45; touch {escaped}"
        files_before = {path for path in self.root.rglob("*") if path.is_file()}

        result = self._run_cli(
            "--mode",
            "project",
            "--task-category",
            "security",
            "--query-stdin",
            "--json",
            stdin=query,
        )
        files_after = {path for path in self.root.rglob("*") if path.is_file()}
        serialized_files = "\n".join(
            path.read_text(errors="replace") for path in sorted(files_after)
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn(query, result.stdout)
        self.assertNotIn(query, result.stderr)
        self.assertNotIn(query, serialized_files)
        self.assertEqual(files_after, files_before)
        self.assertFalse(escaped.exists())
        invocation = json.loads(self.qmd_log.read_text().splitlines()[0])
        self.assertEqual(invocation["query_sha256"], hashlib.sha256(query.encode()).hexdigest())

    def test_empty_and_invalid_qmd_outputs_are_distinct_non_successes(self) -> None:
        empty = self._run_cli(
            "--task-category", "general", "--json", "nothing", fake_mode="empty"
        )
        invalid = self._run_cli(
            "--task-category", "general", "--json", "broken", fake_mode="invalid"
        )
        empty_output = json.loads(empty.stdout)
        invalid_output = json.loads(invalid.stdout)

        self.assertEqual(empty.returncode, 20)
        self.assertEqual(empty_output["status"], "insufficient")
        self.assertEqual(empty_output["data"]["retrieval"]["status"], "empty")
        self.assertEqual(invalid.returncode, 40)
        self.assertEqual(invalid_output["status"], "blocked")
        self.assertEqual(invalid_output["data"]["retrieval"]["status"], "invalid")

    def test_timeout_is_a_distinct_engine_failure(self) -> None:
        def timeout_runner(
            arguments: list[str], **_: object
        ) -> subprocess.CompletedProcess[str]:
            raise subprocess.TimeoutExpired(arguments, 0.01)

        previous_cwd = Path.cwd()
        previous_qmd = os.environ.get("SKILLZ_MEMORY_QMD")
        try:
            os.chdir(self.repo)
            os.environ["SKILLZ_MEMORY_QMD"] = str(self.qmd)
            outcome = run_context(
                mode=RetrievalMode.PROJECT,
                task_category=TaskCategory.GENERAL,
                query="timeout",
                runner=timeout_runner,
                timeout_seconds=0.01,
            )
        finally:
            os.chdir(previous_cwd)
            if previous_qmd is None:
                os.environ.pop("SKILLZ_MEMORY_QMD", None)
            else:
                os.environ["SKILLZ_MEMORY_QMD"] = previous_qmd

        self.assertEqual(outcome.status, "blocked")
        self.assertEqual(outcome.exit_code, 40)
        self.assertEqual(outcome.retrieval_status.value, "timeout")
        self.assertEqual(outcome.errors[0]["code"], "qmd_timeout")

    def test_query_stdin_is_bounded_before_qmd_is_invoked(self) -> None:
        result = self._run_cli(
            "--task-category",
            "general",
            "--query-stdin",
            "--json",
            stdin="x" * (16 * 1024 + 1),
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("query must not exceed 16384 characters", result.stderr)
        self.assertEqual(self.qmd_log.read_text(), "")


if __name__ == "__main__":
    unittest.main()
