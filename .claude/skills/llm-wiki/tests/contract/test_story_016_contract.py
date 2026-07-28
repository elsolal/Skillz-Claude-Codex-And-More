from __future__ import annotations

import io
import json
import sys
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT))

from memory_cli.receipts import WeeklyReportOutcome  # noqa: E402
from memory_cli.render_human import render_weekly_report_human  # noqa: E402
from memory_cli.render_json import weekly_report_envelope  # noqa: E402
from memory_cli.render_markdown import (  # noqa: E402
    ReportExportError,
    render_weekly_report_markdown,
    scan_markdown_export,
)


EXPECTED = SKILL_ROOT / "expected_outputs" / "memory"


def _outcome() -> WeeklyReportOutcome:
    return WeeklyReportOutcome(
        status="ready",
        exit_code=0,
        project_id="skillz-claude",
        period_start="2026-07-21T12:00:00Z",
        period_end="2026-07-28T12:00:00Z",
        efficiency={
            "context_events": 2,
            "estimated_context_tokens": {"median": 600.0, "p95": 800.0},
            "duration_ms": {"median": 200.0, "p95": 300.0},
        },
        quality=None,
        reliability={
            "fallback_rate": 0.0,
            "insufficiency_rate": 0.0,
            "freshness": {"fresh": 2, "stale": 0, "unknown": 0},
            "activation_errors": 0,
        },
        usage_funnel={
            "retrieved": 2,
            "read": 2,
            "used": 1,
            "cited": 1,
            "read_rate": 1.0,
            "used_rate": 0.5,
            "cited_rate": 1.0,
        },
        decisions=(
            {
                "debt_id": "con_20260727T120002000000Z_0123456789abcdef",
                "priority": "P0",
                "risk": "high",
                "category": "architecture",
                "observed_impact_count": 1,
                "memory": {
                    "docid": "#a1b2c3",
                    "path": "wiki/entities/skillz-claude.md",
                },
                "repository": {
                    "path": "src/current-contract.py",
                    "evidence_type": "contract",
                },
                "actions": {
                    "fix": "memory finish con_20260727T120002000000Z_0123456789abcdef --debt-action fix",
                    "ignore": "memory finish con_20260727T120002000000Z_0123456789abcdef --debt-action ignore --reason <reason_slug>",
                    "snooze": "memory finish con_20260727T120002000000Z_0123456789abcdef --debt-action snooze --until YYYY-MM-DD",
                },
            },
        ),
        appendix={"remaining_count": 0, "by_risk": {}, "by_category": {}},
        review_budget_minutes=10,
    )


class Story016OutputContractTests(unittest.TestCase):
    def test_human_json_and_markdown_preserve_the_same_bounded_decision(self) -> None:
        outcome = _outcome()
        human = io.StringIO()
        render_weekly_report_human(outcome, stream=human)
        envelope = weekly_report_envelope(outcome)
        markdown = render_weekly_report_markdown(outcome)

        self.assertEqual(
            envelope,
            json.loads((EXPECTED / "report-weekly.json").read_text(encoding="utf-8")),
        )
        self.assertEqual(
            human.getvalue(),
            (EXPECTED / "report-weekly-human.txt").read_text(encoding="utf-8"),
        )
        self.assertEqual(
            markdown,
            (EXPECTED / "report-weekly.md").read_text(encoding="utf-8"),
        )
        self.assertEqual(envelope["command"], "report.weekly")
        self.assertEqual(envelope["data"]["review"]["decision_count"], 1)
        self.assertIn("Review budget: 10 minutes · 1 decision", human.getvalue())
        self.assertIn("P0 · HIGH · architecture", human.getvalue())
        self.assertIn("# Memory Weekly · skillz-claude", markdown)
        self.assertIn("## Decisions", markdown)
        self.assertIn("--debt-action fix", markdown)
        serialized = json.dumps(envelope) + human.getvalue() + markdown
        for forbidden in ('"prompt":', '"response":', '"snippet":', "/Users/"):
            self.assertNotIn(forbidden, serialized)

    def test_final_markdown_scanner_rejects_content_secrets_and_absolute_paths(
        self,
    ) -> None:
        forbidden_values = (
            "prompt: private task",
            "response: private answer",
            "snippet: raw page body",
            "/Users/example/private.md",
            r"C:\Users\example\private.md",
            r"\\server\share\private.md",
            "sk-proj-abcdefghijklmnopqrstuvwxyz123456",
        )
        for value in forbidden_values:
            with self.subTest(value=value), self.assertRaises(ReportExportError):
                scan_markdown_export(f"# Weekly\n\n{value}\n")


if __name__ == "__main__":
    unittest.main()
