from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from integration.test_context_cli import ContextCliIntegrationTests, SKILL_ROOT
from memory_cli import cli as memory_cli
from memory_cli.contracts import RetrievalMode, TaskCategory
from memory_cli.qmd_adapter import QmdSearchStatus
from memory_cli.receipts import ContextInitialReceipt, ContextOutcome


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

    def test_finish_appends_one_attestation_without_mutating_parent(self) -> None:
        context = self.fixture._run_cli(
            "--mode",
            "project",
            "--task-category",
            "architecture",
            "--json",
            "attested context",
        )
        parent_id = json.loads(context.stdout)["event_id"]
        event_file = next(self.fixture.state_dir.rglob("*.jsonl"))
        parent_line = event_file.read_text().splitlines()[0]

        finish = self.fixture._run_memory_cli(
            "finish",
            parent_id,
            "--used",
            "#dfec5e",
            "--cited",
            "#dfec5e",
            "--impact-code",
            "project_convention_applied",
            "--json",
        )
        output = json.loads(finish.stdout)
        lines = event_file.read_text().splitlines()
        attestation = json.loads(lines[1])

        self.assertEqual(finish.returncode, 0, finish.stderr)
        self.assertEqual(lines[0], parent_line)
        self.assertEqual(len(lines), 2)
        self.assertEqual(attestation["event_type"], "usage_attested")
        self.assertEqual(attestation["parent_event_id"], parent_id)
        self.assertRegex(output["event_id"], r"^att_\d{8}T\d{12}Z_[0-9a-f]{16}$")
        self.assertEqual(output["data"]["measured"]["retrieved"], 2)
        self.assertEqual(output["data"]["attested"]["used"], ["#dfec5e"])
        self.assertEqual(
            output["data"]["attested"]["impact_codes"],
            ["project_convention_applied"],
        )

    def test_finish_rejects_unknown_docid_and_second_attestation_without_append(self) -> None:
        context = self.fixture._run_cli(
            "--mode",
            "project",
            "--task-category",
            "architecture",
            "--json",
            "single attestation",
        )
        parent_id = json.loads(context.stdout)["event_id"]
        event_file = next(self.fixture.state_dir.rglob("*.jsonl"))

        invalid = self.fixture._run_memory_cli(
            "finish", parent_id, "--used", "#missing", "--json"
        )
        invalid_output = json.loads(invalid.stdout)
        self.assertEqual(invalid.returncode, 50)
        self.assertIn("#missing", invalid_output["errors"][0]["message"])
        self.assertEqual(len(event_file.read_text().splitlines()), 1)

        first = self.fixture._run_memory_cli("finish", parent_id, "--json")
        duplicate = self.fixture._run_memory_cli("finish", parent_id, "--json")
        duplicate_output = json.loads(duplicate.stdout)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(duplicate.returncode, 50)
        self.assertEqual(
            duplicate_output["errors"][0]["code"], "parent_already_attested"
        )
        self.assertEqual(len(event_file.read_text().splitlines()), 2)

    def test_finish_accepts_structured_citation_only(self) -> None:
        context = self.fixture._run_cli(
            "--mode",
            "project",
            "--task-category",
            "architecture",
            "--json",
            "citation-only context",
        )
        parent_id = json.loads(context.stdout)["event_id"]

        finish = self.fixture._run_memory_cli(
            "finish",
            parent_id,
            "--cited",
            "#dfec5e",
            "--citation-only",
            "#dfec5e",
            "--json",
        )
        output = json.loads(finish.stdout)

        self.assertEqual(finish.returncode, 0, finish.stderr)
        self.assertEqual(output["data"]["attested"]["used"], [])
        self.assertEqual(output["data"]["attested"]["cited"], ["#dfec5e"])
        self.assertEqual(
            output["data"]["attested"]["citation_only"], ["#dfec5e"]
        )

    def test_concurrent_finish_allows_exactly_one_attestation(self) -> None:
        context = self.fixture._run_cli(
            "--mode",
            "project",
            "--task-category",
            "architecture",
            "--json",
            "concurrent finish",
        )
        parent_id = json.loads(context.stdout)["event_id"]

        def run_finish(_: int) -> subprocess.CompletedProcess[str]:
            return self.fixture._run_memory_cli("finish", parent_id, "--json")

        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(run_finish, range(8)))

        self.assertEqual(sum(result.returncode == 0 for result in results), 1)
        self.assertTrue(
            all(result.returncode in {0, 50} for result in results), results
        )
        event_file = next(self.fixture.state_dir.rglob("*.jsonl"))
        events = [json.loads(line) for line in event_file.read_text().splitlines()]
        self.assertEqual(len(events), 2)
        self.assertEqual(
            [event["event_type"] for event in events],
            ["context_completed", "usage_attested"],
        )

    def test_context_reuses_the_preflight_manifest_path_for_event_storage(self) -> None:
        initial = ContextInitialReceipt(
            project_id="skillz-claude",
            mode=RetrievalMode.HISTORICAL,
            task_category=TaskCategory.HISTORICAL,
            planned_route=("elsolal-wiki",),
            target_tokens=6000,
            hard_tokens=9000,
        )
        outcome = ContextOutcome(
            status="blocked",
            exit_code=31,
            project_id="skillz-claude",
            mode=RetrievalMode.HISTORICAL,
            task_category=TaskCategory.HISTORICAL,
            route=("elsolal-wiki",),
            retrieval_status=QmdSearchStatus.ERROR,
            duration_ms=None,
            hits=(),
            initial_receipt=initial,
        )
        manifest_path = self.fixture.repo / ".agents" / "memory.yaml"

        with (
            patch.object(
                memory_cli,
                "discover_manifest",
                side_effect=[manifest_path, AssertionError("manifest rediscovered")],
            ) as discovery,
            patch.object(memory_cli, "run_context", return_value=outcome),
            patch.object(memory_cli, "append_event"),
            patch.object(memory_cli, "render_context_json"),
        ):
            exit_code = memory_cli._run_context_command(
                mode="historical",
                task_category="historical",
                query="history",
                fallback_on_ambiguous=False,
                risk_reason=None,
                explain=False,
                json_output=True,
            )

        self.assertEqual(exit_code, 31)
        self.assertEqual(discovery.call_count, 1)

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
