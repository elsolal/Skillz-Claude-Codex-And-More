from __future__ import annotations

import json
import re
import unittest

from integration.test_context_cli import ContextCliIntegrationTests, SKILL_ROOT


EXPECTED = SKILL_ROOT / "expected_outputs" / "memory"


class FinishReceiptContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = ContextCliIntegrationTests(
            methodName="test_context_queries_project_first_and_normalizes_hits"
        )
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def _context_event_id(self) -> str:
        result = self.fixture._run_cli(
            "--mode",
            "project",
            "--task-category",
            "architecture",
            "--json",
            "finish receipt",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return str(json.loads(result.stdout)["event_id"])

    def test_json_receipt_separates_measured_and_attested_fields(self) -> None:
        parent_id = self._context_event_id()
        result = self.fixture._run_memory_cli(
            "finish",
            parent_id,
            "--used",
            "#dfec5e",
            "--cited",
            "#dfec5e",
            "--impact-code",
            "validation_command_reused",
            "--json",
        )
        output = json.loads(result.stdout)

        self.assertEqual(result.returncode, 0, result.stderr)
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
        self.assertEqual(output["command"], "finish")
        self.assertEqual(output["status"], "ready")
        self.assertEqual(output["data"]["parent_event_id"], parent_id)
        self.assertEqual(
            list(output["data"]),
            ["parent_event_id", "measured", "attested"],
        )
        self.assertEqual(
            output["data"]["attested"],
            {
                "impact_taxonomy_version": "impact-v1",
                "used": ["#dfec5e"],
                "cited": ["#dfec5e"],
                "citation_only": [],
                "impact_codes": ["validation_command_reused"],
            },
        )
        output["event_id"] = "<event-id>"
        output["data"]["parent_event_id"] = "<parent-event-id>"
        output["data"]["measured"]["duration_ms"] = "<duration>"
        self.assertEqual(
            output,
            json.loads((EXPECTED / "finish-ready.json").read_text()),
        )

    def test_empty_human_receipt_is_explicitly_not_impact_success(self) -> None:
        parent_id = self._context_event_id()
        result = self.fixture._run_memory_cli("finish", parent_id)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(
            result.stdout.splitlines()[0],
            r"^Memory final · event att_\d{8}T\d{12}Z_[0-9a-f]{16}$",
        )
        self.assertIn("Measured:", result.stdout)
        self.assertIn("Attested: 0 used · 0 cited", result.stdout)
        self.assertIn("Impact: none observed", result.stdout)
        self.assertNotIn("Impact: success", result.stdout)
        self.assertNotIn("Memory ready", result.stdout)
        self.assertIsNone(re.search(r"\b(success|successful)\b", result.stdout, re.I))
        receipt_snapshot = re.sub(
            r"event att_\d{8}T\d{12}Z_[0-9a-f]{16}",
            "event <event-id>",
            result.stdout,
        )
        receipt_snapshot = re.sub(r"\d+ms$", "<duration>", receipt_snapshot, flags=re.M)
        self.assertEqual(
            receipt_snapshot,
            (EXPECTED / "finish-receipt-human.txt").read_text(),
        )


if __name__ == "__main__":
    unittest.main()
