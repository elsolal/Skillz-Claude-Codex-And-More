from __future__ import annotations

import io
import json
import os
import re
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from integration import test_context_cli as context_support
from memory_cli.context import run_context
from memory_cli.contracts import RetrievalMode, TaskCategory
from memory_cli.receipts import ContextInitialReceipt
from memory_cli.render_human import render_context_initial


EXPECTED = context_support.EXPECTED


class TtyBuffer(io.StringIO):
    def isatty(self) -> bool:
        return True


class ContextReceiptContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = context_support.ContextCliIntegrationTests(
            methodName="test_context_queries_project_first_and_normalizes_hits"
        )
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def test_initial_receipt_is_emitted_before_retrieval_without_query_content(self) -> None:
        events: list[object] = []

        def recording_runner(
            arguments: list[str], **kwargs: object
        ) -> subprocess.CompletedProcess[str]:
            events.append(("runner", arguments[1]))
            return subprocess.run(arguments, **kwargs)

        previous_cwd = Path.cwd()
        previous_qmd = os.environ.get("SKILLZ_MEMORY_QMD")
        try:
            os.chdir(self.fixture.repo)
            os.environ["SKILLZ_MEMORY_QMD"] = str(self.fixture.qmd)
            outcome = run_context(
                mode=RetrievalMode.PROJECT,
                task_category=TaskCategory.ARCHITECTURE,
                query="private receipt query",
                runner=recording_runner,
                on_initial_receipt=lambda receipt: events.append(("receipt", receipt)),
            )
        finally:
            os.chdir(previous_cwd)
            if previous_qmd is None:
                os.environ.pop("SKILLZ_MEMORY_QMD", None)
            else:
                os.environ["SKILLZ_MEMORY_QMD"] = previous_qmd

        self.assertEqual(outcome.status, "sufficient")
        self.assertEqual(events[0][0], "receipt")
        initial = events[0][1]
        self.assertEqual(initial.project_id, "skillz-claude")
        self.assertEqual(initial.mode, RetrievalMode.PROJECT)
        self.assertEqual(initial.task_category, TaskCategory.ARCHITECTURE)
        self.assertEqual(initial.planned_route, ("elsolal-wiki", "shared-wiki"))
        self.assertEqual(initial.target_tokens, 2500)
        self.assertEqual(initial.hard_tokens, 4000)
        self.assertNotIn("private receipt query", repr(initial))

    def test_json_receipts_are_stable_and_initial_progress_stays_on_stderr(self) -> None:
        query = "private-json-receipt-query"
        result = self.fixture._run_cli(
            "--mode",
            "project",
            "--task-category",
            "architecture",
            "--json",
            query,
        )
        output = json.loads(result.stdout)

        self.assertEqual(
            list(output),
            [
                "schema_version",
                "command",
                "status",
                "project_id",
                "event_id",
                "data",
                "warnings",
                "errors",
            ],
        )
        self.assertIsNone(output["event_id"])
        self.assertEqual(list(output["data"]["receipt"]), ["initial", "final"])
        self.assertEqual(
            output["data"]["receipt"]["initial"],
            {
                "project_id": "skillz-claude",
                "mode": "project",
                "task_category": "architecture",
                "planned_route": ["elsolal-wiki", "shared-wiki"],
                "budget": {"target_tokens": 2500, "hard_tokens": 4000},
                "status": "retrieving",
            },
        )
        final = output["data"]["receipt"]["final"]
        self.assertEqual(
            list(final),
            [
                "status",
                "retrieved",
                "read",
                "estimated_tokens",
                "budget_tokens",
                "duration_ms",
                "freshness",
                "fallback",
            ],
        )
        self.assertEqual(final["status"], "sufficient")
        self.assertEqual(final["retrieved"], 2)
        self.assertEqual(final["read"], 1)
        self.assertIsInstance(final["duration_ms"], int)
        self.assertEqual(final["freshness"], "fresh")
        self.assertEqual(final["fallback"], {"used": False, "reason_codes": []})
        self.assertIn("Memory · PROJECT · skillz-claude", result.stderr)
        self.assertIn("Status: retrieving project context", result.stderr)
        self.assertNotIn(query, result.stdout + result.stderr)

    def test_human_receipts_preserve_fields_without_color_or_tty(self) -> None:
        query = "private-human-receipt-query"
        result = self.fixture._run_cli(
            "--mode",
            "project",
            "--task-category",
            "architecture",
            query,
            extra_env={"NO_COLOR": "1"},
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("\x1b[", result.stdout + result.stderr)
        self.assertNotIn(query, result.stdout + result.stderr)
        receipt_snapshot = "\n".join(
            [*result.stderr.splitlines(), "---", *result.stdout.splitlines()[:4]]
        ) + "\n"
        receipt_snapshot = re.sub(
            r"\d+ms$", "<duration>", receipt_snapshot, flags=re.MULTILINE
        )
        self.assertEqual(
            receipt_snapshot,
            (EXPECTED / "context-receipts-human.txt").read_text(),
        )

    def test_tty_initial_receipt_keeps_every_functional_label(self) -> None:
        receipt = ContextInitialReceipt(
            project_id="skillz-claude",
            mode=RetrievalMode.PROJECT,
            task_category=TaskCategory.ARCHITECTURE,
            planned_route=("elsolal-wiki", "shared-wiki"),
            target_tokens=2500,
            hard_tokens=4000,
        )
        stream = TtyBuffer()

        with patch.dict(os.environ, {}, clear=False):
            render_context_initial(receipt, stream=stream)

        output = stream.getvalue()
        self.assertTrue(stream.isatty())
        self.assertIn("Memory · PROJECT · skillz-claude", output)
        self.assertIn("Route: elsolal-wiki -> shared-wiki", output)
        self.assertIn("Budget: 2,500 estimated tokens", output)
        self.assertIn("task: architecture", output)
        self.assertIn("Status: retrieving project context", output)

    def test_degraded_human_receipt_never_masks_the_state_as_success(self) -> None:
        result = self.fixture._run_cli(
            "--mode",
            "minimal",
            "--task-category",
            "general",
            "local context",
            qmd=self.fixture.root / "missing-qmd",
        )

        self.assertEqual(result.returncode, 10, result.stderr)
        self.assertEqual(
            result.stdout.splitlines()[0],
            "Memory degraded · project-only · event not recorded",
        )
        self.assertNotIn("Memory ready", result.stdout)
        self.assertIn("Freshness: unknown", result.stdout)
        self.assertIn("Fallback: not used", result.stdout)


if __name__ == "__main__":
    unittest.main()
