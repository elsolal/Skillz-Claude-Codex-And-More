from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from integration.test_context_cli import ContextCliIntegrationTests, SKILL_ROOT


class EventStoreCliIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = ContextCliIntegrationTests(
            methodName="test_context_queries_project_first_and_normalizes_hits"
        )
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def test_context_persists_one_event_and_returns_the_same_id(self) -> None:
        result = self.fixture._run_cli(
            "--mode",
            "project",
            "--task-category",
            "architecture",
            "--json",
            "private query that must not be stored",
        )
        output = json.loads(result.stdout)
        event_files = list(self.fixture.state_dir.rglob("*.jsonl"))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(output["event_id"], r"^mem_\d{8}T\d{12}Z_[0-9a-f]{16}$")
        self.assertEqual(len(event_files), 1)
        events = [json.loads(line) for line in event_files[0].read_text().splitlines()]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_id"], output["event_id"])
        self.assertNotIn("private query", event_files[0].read_text())

    def test_completed_insufficient_and_blocked_attempts_are_also_recorded(self) -> None:
        insufficient = self.fixture._run_cli(
            "--mode",
            "project",
            "--task-category",
            "general",
            "--json",
            "no matching evidence",
            fake_mode="empty",
        )
        blocked = self.fixture._run_cli(
            "--mode",
            "historical",
            "--task-category",
            "historical",
            "--json",
            "history without qmd",
            qmd=self.fixture.root / "missing-qmd",
        )
        insufficient_output = json.loads(insufficient.stdout)
        blocked_output = json.loads(blocked.stdout)

        self.assertEqual(insufficient.returncode, 20, insufficient.stderr)
        self.assertEqual(blocked.returncode, 31, blocked.stderr)
        event_file = next(self.fixture.state_dir.rglob("*.jsonl"))
        events = [json.loads(line) for line in event_file.read_text().splitlines()]
        self.assertEqual(
            [event["payload"]["status"] for event in events],
            ["insufficient", "blocked"],
        )
        self.assertEqual(
            [event["event_id"] for event in events],
            [insufficient_output["event_id"], blocked_output["event_id"]],
        )

    def test_concurrent_processes_append_complete_json_with_unique_ids(self) -> None:
        worker = (
            "import json, os; "
            "from datetime import datetime, timezone; "
            "from pathlib import Path; "
            "from memory_cli.events import build_context_event, append_event; "
            "metadata=json.loads(os.environ['EVENT_METADATA']); "
            "event=build_context_event(metadata); "
            "append_event(event, state_dir=Path(os.environ['STATE_DIR']), "
            "project_root=Path(os.environ['PROJECT_ROOT']))"
        )
        metadata = {
            "project_id": "skillz-claude",
            "mode": "project",
            "task_category": "general",
            "status": "sufficient",
            "route": ["elsolal-wiki"],
            "retrieved": [],
            "read": [],
            "estimated_context_tokens": 0,
            "estimator_version": "utf8_bytes_div_4_v1",
            "budget_tokens": 2500,
            "duration_ms": 1,
            "freshness": "unknown",
            "fallback_reason_codes": [],
            "risk_reason": None,
        }
        environment = os.environ.copy()
        environment.update(
            {
                "PYTHONPATH": str(SKILL_ROOT),
                "EVENT_METADATA": json.dumps(metadata),
                "STATE_DIR": str(self.fixture.state_dir),
                "PROJECT_ROOT": str(self.fixture.repo),
            }
        )

        def run_worker(_: int) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                [sys.executable, "-c", worker],
                env=environment,
                check=False,
                text=True,
                capture_output=True,
            )

        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(run_worker, range(24)))
        self.assertTrue(all(result.returncode == 0 for result in results), results)

        event_file = next(self.fixture.state_dir.rglob("*.jsonl"))
        events = [json.loads(line) for line in event_file.read_text().splitlines()]
        self.assertEqual(len(events), 24)
        self.assertEqual(len({event["event_id"] for event in events}), 24)

    def test_purge_nominal_and_force_are_scriptable_and_project_scoped(self) -> None:
        context = self.fixture._run_cli(
            "--mode",
            "project",
            "--task-category",
            "architecture",
            "--json",
            "event to purge",
        )
        self.assertEqual(context.returncode, 0, context.stderr)

        nominal = self.fixture._run_memory_cli("purge", "--json")
        nominal_output = json.loads(nominal.stdout)
        self.assertEqual(nominal.returncode, 0, nominal.stderr)
        self.assertEqual(nominal_output["data"]["deleted_events"], 0)
        self.assertEqual(nominal_output["data"]["retained_events"], 1)
        self.assertEqual(
            nominal_output,
            json.loads(
                (SKILL_ROOT / "expected_outputs" / "memory" / "purge-ready.json").read_text()
            ),
        )

        forced = self.fixture._run_memory_cli("purge", "--force", "--json")
        forced_output = json.loads(forced.stdout)
        self.assertEqual(forced.returncode, 0, forced.stderr)
        self.assertEqual(forced_output["data"]["deleted_events"], 1)
        self.assertFalse(
            (self.fixture.state_dir / "events" / "skillz-claude").exists()
        )

    def test_telemetry_failure_preserves_context_and_returns_exit_50(self) -> None:
        result = self.fixture._run_cli(
            "--mode",
            "project",
            "--task-category",
            "architecture",
            "--json",
            "context survives telemetry failure",
            extra_env={"SKILLZ_MEMORY_STATE_DIR": str(self.fixture.repo / ".state")},
        )
        output = json.loads(result.stdout)

        self.assertEqual(result.returncode, 50, result.stderr)
        self.assertEqual(output["status"], "sufficient")
        self.assertIsNone(output["event_id"])
        self.assertIn("context", output["data"])
        self.assertEqual(output["errors"][-1]["code"], "state_dir_in_project")


if __name__ == "__main__":
    unittest.main()
