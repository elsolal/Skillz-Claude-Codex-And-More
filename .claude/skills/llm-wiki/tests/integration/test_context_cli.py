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
        (self.repo / ".agents").mkdir(parents=True)
        (self.vault / "wiki" / "entities").mkdir(parents=True)
        (self.vault / "wiki" / "entities" / "project.md").write_text("# Project\n")
        self._write_activation()
        self.qmd_log = self.root / "qmd-invocations.jsonl"
        self.qmd_log.write_text("")
        self.qmd = self._make_qmd()

    def _write_activation(self) -> None:
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
            "fallbacks": [],
            "budgets": {
                "minimal": {"target_tokens": 800, "hard_tokens": 1200},
                "project": {"target_tokens": 2500, "hard_tokens": 4000},
                "historical": {"target_tokens": 6000, "hard_tokens": 9000},
            },
            "policy": {
                "semantic_retrieval": "explicit",
                "full_index_fallback": True,
                "retention_days": 30,
            },
            "golden": {
                "visible_path": ".agents/memory/golden.json",
                "quality_rubric": ".agents/memory/quality-rubric.json",
            },
        }
        projection = {
            "schema_version": 1,
            "principal": {"role": "owner"},
            "stores": {"project": {"root": str(self.vault)}},
        }
        (self.repo / ".agents" / "memory.yaml").write_text(json.dumps(manifest))
        (self.repo / ".agents" / "memory.local.json").write_text(json.dumps(projection))
        subprocess.run(["git", "init", "-b", "main"], cwd=self.repo, check=True, capture_output=True)

    def _make_qmd(self) -> Path:
        binary = self.root / "qmd-fixture"
        binary.write_text(
            "#!/usr/bin/env python3\n"
            "import hashlib, json, os, sys\n"
            f"fixture = {str(SEARCH_FIXTURE)!r}\n"
            f"log = {str(self.qmd_log)!r}\n"
            "query = sys.argv[2] if len(sys.argv) > 2 else ''\n"
            "collection = sys.argv[sys.argv.index('-c') + 1] if '-c' in sys.argv else None\n"
            "with open(log, 'a', encoding='utf-8') as stream:\n"
            "    stream.write(json.dumps({'command': sys.argv[1], 'collection': collection, "
            "'query_sha256': hashlib.sha256(query.encode()).hexdigest()}) + '\\n')\n"
            "mode = os.environ.get('FAKE_QMD_MODE', 'ready')\n"
            "if mode == 'empty': print('[]')\n"
            "elif mode == 'invalid': print('{not-json')\n"
            "else:\n"
            "    with open(fixture, encoding='utf-8') as stream: print(stream.read())\n"
        )
        binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
        return binary

    def _run_cli(
        self,
        *arguments: str,
        stdin: str | None = None,
        fake_mode: str = "ready",
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment.update(
            {
                "PYTHONPATH": str(SKILL_ROOT),
                "SKILLZ_MEMORY_QMD": str(self.qmd),
                "FAKE_QMD_MODE": fake_mode,
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
        self.assertEqual(output["status"], "ready")
        self.assertEqual(output["data"]["route"], ["elsolal-wiki"])
        self.assertEqual(output["data"]["retrieval"]["status"], "ready")
        self.assertEqual(output["data"]["retrieval"]["hits"][0]["path"], "entities/skillz-claude.md")
        self.assertNotIn("agentic coding", result.stdout)
        self.assertIsInstance(output["data"]["retrieval"]["duration_ms"], int)
        self.assertEqual(invocation["command"], "search")
        self.assertEqual(invocation["collection"], "elsolal-wiki")

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
