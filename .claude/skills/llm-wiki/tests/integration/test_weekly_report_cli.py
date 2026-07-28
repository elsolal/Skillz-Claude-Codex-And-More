from __future__ import annotations

import hashlib
import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from integration import test_context_cli as context_support


def _tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


class WeeklyReportCliIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = context_support.ContextCliIntegrationTests(
            methodName="test_context_queries_project_first_and_normalizes_hits"
        )
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        (self.fixture.repo / ".claude").mkdir()
        (self.fixture.repo / ".claude" / "project-memory.md").write_text(
            "Repository-first memory contract.\n",
            encoding="utf-8",
        )

    def _open_debt(self) -> str:
        context = self.fixture._run_cli(
            "--mode",
            "project",
            "--task-category",
            "architecture",
            "--json",
            "weekly report integration",
        )
        self.assertEqual(context.returncode, 0, context.stderr)
        parent_id = str(json.loads(context.stdout)["event_id"])
        conflict = self.fixture._run_memory_cli(
            "finish",
            parent_id,
            "--used",
            "#dfec5e",
            "--conflict-docid",
            "#dfec5e",
            "--repo-evidence",
            ".claude/project-memory.md",
            "--evidence-type",
            "contract",
            "--conflict-category",
            "architecture",
            "--conflict-risk",
            "high",
            "--prepare-debt",
            "--json",
        )
        self.assertEqual(conflict.returncode, 21, conflict.stderr)
        return str(json.loads(conflict.stdout)["event_id"])

    def test_weekly_report_is_project_scoped_and_exports_scanned_markdown(self) -> None:
        before_vault = _tree_hash(self.fixture.vault)
        debt_id = self._open_debt()
        event_file = next(
            (self.fixture.state_dir / "events" / "skillz-claude").glob("*.jsonl")
        )
        other = json.loads(event_file.read_text(encoding="utf-8").splitlines()[0])
        other["event_id"] = (
            "mem_20260728T010203000000Z_aaaaaaaaaaaaaaaa"
        )
        other["project_id"] = "other-project"
        with event_file.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(other, separators=(",", ":")) + "\n")

        result = self.fixture._run_memory_cli("report", "--weekly", "--json")
        output = json.loads(result.stdout)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output["command"], "report.weekly")
        self.assertEqual(output["project_id"], "skillz-claude")
        self.assertEqual(output["data"]["review"]["decision_count"], 1)
        self.assertEqual(output["data"]["decisions"][0]["debt_id"], debt_id)
        self.assertEqual(output["data"]["privacy"]["raw_cross_project_events"], 0)

        export = self.fixture.root / "weekly.md"
        exported = self.fixture._run_memory_cli(
            "report",
            "--weekly",
            "--export-markdown",
            str(export),
        )
        self.assertEqual(exported.returncode, 0, exported.stderr)
        markdown = export.read_text(encoding="utf-8")
        self.assertIn("# Memory Weekly · skillz-claude", markdown)
        self.assertIn(debt_id, markdown)
        self.assertNotIn("other-project", markdown)
        self.assertNotIn(str(self.fixture.repo), markdown)
        self.assertEqual(_tree_hash(self.fixture.vault), before_vault)

    def test_existing_append_only_action_removes_debt_from_the_next_report(self) -> None:
        debt_id = self._open_debt()
        fixed = self.fixture._run_memory_cli(
            "finish",
            debt_id,
            "--debt-action",
            "fix",
            "--json",
        )
        self.assertEqual(fixed.returncode, 0, fixed.stderr)

        report = self.fixture._run_memory_cli("report", "--weekly", "--json")
        output = json.loads(report.stdout)

        self.assertEqual(report.returncode, 0, report.stderr)
        self.assertEqual(output["data"]["decisions"], [])
        self.assertEqual(output["data"]["review"]["decision_count"], 0)

    def test_nominal_pilot_path_is_bounded_to_ten_minutes(self) -> None:
        started_at = datetime.now(timezone.utc)
        debt_ids = [self._open_debt() for _ in range(7)]

        report = self.fixture._run_memory_cli("report", "--weekly", "--json")
        output = json.loads(report.stdout)

        self.assertEqual(report.returncode, 0, report.stderr)
        self.assertEqual(output["data"]["review"]["decision_count"], 7)
        self.assertEqual(output["data"]["review"]["budget_minutes"], 10)
        for debt_id in debt_ids:
            fixed = self.fixture._run_memory_cli(
                "finish",
                debt_id,
                "--debt-action",
                "fix",
                "--json",
            )
            self.assertEqual(fixed.returncode, 0, fixed.stderr)
        reviewed = self.fixture._run_memory_cli("report", "--weekly", "--json")
        self.assertEqual(reviewed.returncode, 0, reviewed.stderr)
        self.assertEqual(json.loads(reviewed.stdout)["data"]["decisions"], [])
        elapsed = datetime.now(timezone.utc) - started_at
        self.assertLess(elapsed, timedelta(minutes=10))

    def test_invalid_naive_run_timestamp_is_blocked_without_traceback(self) -> None:
        run_id = "run_20260728T120000000000Z_0123456789abcdef"
        run_dir = self.fixture.state_dir / "runs" / "skillz-claude"
        run_dir.mkdir(parents=True)
        (run_dir / f"{run_id}.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "run_id": run_id,
                    "occurred_at": "2026-07-28T12:00:00",
                    "project_id": "skillz-claude",
                    "estimator_version": "utf8_bytes_div_4_v1",
                    "cases": [],
                    "aggregate": {
                        "retrieval_hit_rate": 0.95,
                        "fallback_rate": 0.0,
                        "median_context_reduction": 0.55,
                    },
                }
            ),
            encoding="utf-8",
        )

        result = self.fixture._run_memory_cli("report", "--weekly", "--json")
        output = json.loads(result.stdout)

        self.assertEqual(result.returncode, 50, result.stderr)
        self.assertEqual(output["status"], "blocked")
        self.assertEqual(output["errors"][0]["code"], "quality_run_invalid")
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
