from __future__ import annotations

import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT))

from memory_cli.conflicts import (  # noqa: E402
    build_memory_conflict_event,
    build_memory_debt_action_event,
)
from memory_cli.contracts import (  # noqa: E402
    ConflictCategory,
    ConflictEvidenceType,
    ConflictRisk,
    DebtAction,
)
from memory_cli.events import (  # noqa: E402
    build_context_event,
    build_usage_attestation_event,
)
from memory_cli.report import build_weekly_report  # noqa: E402
from unit.test_events import context_metadata  # noqa: E402


NOW = datetime(2026, 7, 28, 12, tzinfo=timezone.utc)


def _context(
    *,
    occurred_at: datetime,
    tokens: int = 800,
    duration_ms: int = 1000,
    route: tuple[str, ...] = ("elsolal-wiki",),
    status: str = "sufficient",
    freshness: str = "fresh",
) -> dict[str, object]:
    metadata = context_metadata()
    metadata.update(
        {
            "estimated_context_tokens": tokens,
            "duration_ms": duration_ms,
            "route": list(route),
            "status": status,
            "freshness": freshness,
            "fallback_reason_codes": (
                ["insufficient_coverage"] if len(route) > 1 else []
            ),
        }
    )
    return build_context_event(metadata, occurred_at=occurred_at)


def _debt_chain(
    *,
    occurred_at: datetime,
    risk: ConflictRisk,
    impacts: tuple[str, ...] = (),
    action: DebtAction | None = None,
    snooze_until: str | None = None,
) -> list[dict[str, object]]:
    parent = _context(occurred_at=occurred_at)
    attestation = build_usage_attestation_event(
        parent,
        used=("#a1b2c3",),
        cited=("#a1b2c3",),
        citation_only=(),
        impact_codes=impacts,
        occurred_at=occurred_at + timedelta(seconds=1),
    )
    conflict = build_memory_conflict_event(
        parent,
        memory_docid="#a1b2c3",
        repository_path="src/current-contract.py",
        evidence_type=ConflictEvidenceType.CONTRACT,
        category=ConflictCategory.ARCHITECTURE,
        risk=risk,
        prepare_debt=True,
        occurred_at=occurred_at + timedelta(seconds=2),
    )
    events = [parent, attestation, conflict]
    if action is not None:
        events.append(
            build_memory_debt_action_event(
                conflict,
                action=action,
                reason="not_actionable" if action is DebtAction.IGNORE else None,
                snooze_until=snooze_until,
                occurred_at=occurred_at + timedelta(seconds=3),
            )
        )
    return events


class WeeklyReportAggregationTests(unittest.TestCase):
    def test_aggregates_weekly_efficiency_quality_fallback_freshness_and_funnel(
        self,
    ) -> None:
        contexts = [
            _context(
                occurred_at=NOW - timedelta(days=2),
                tokens=400,
                duration_ms=100,
            ),
            _context(
                occurred_at=NOW - timedelta(days=1),
                tokens=800,
                duration_ms=300,
                route=("elsolal-wiki", "shared-wiki"),
                status="insufficient",
                freshness="stale",
            ),
            _context(
                occurred_at=NOW - timedelta(days=8),
                tokens=9999,
                duration_ms=9999,
            ),
        ]
        attestation = build_usage_attestation_event(
            contexts[0],
            used=("#a1b2c3",),
            cited=("#a1b2c3",),
            citation_only=(),
            impact_codes=("project_convention_applied",),
            occurred_at=NOW - timedelta(days=2) + timedelta(seconds=1),
        )
        run_id = "run_20260727T120000000000Z_0123456789abcdef"
        run = {
            "schema_version": 1,
            "run_id": run_id,
            "occurred_at": "2026-07-27T12:00:00Z",
            "project_id": "skillz-claude",
            "estimator_version": "utf8_bytes_div_4_v1",
            "cases": [],
            "aggregate": {
                "retrieval_hit_rate": 0.95,
                "fallback_rate": 0.1,
                "median_context_reduction": 0.55,
            },
            "holdout": {
                "case_count": 2,
                "aggregate": {
                    "retrieval_hit_rate": 1.0,
                    "fallback_rate": 0.0,
                    "median_context_reduction": 0.6,
                },
                "details_shared": False,
            },
        }
        quality = {
            "schema_version": 1,
            "project_id": "skillz-claude",
            "run_id": run_id,
            "rubric_version": "quality-v1",
            "baseline_score": 96.0,
            "score": 93.0,
            "reviewer_type": "human",
            "quality_degradation": 0.03125,
        }

        outcome = build_weekly_report(
            project_id="skillz-claude",
            events=[*contexts, attestation],
            runs=[run],
            quality_records=[quality],
            now=NOW,
        )
        data = outcome.data()

        self.assertEqual(outcome.status, "ready")
        self.assertEqual(data["efficiency"]["context_events"], 2)
        self.assertEqual(
            data["efficiency"]["estimated_context_tokens"],
            {"median": 600.0, "p95": 800.0},
        )
        self.assertEqual(data["reliability"]["fallback_rate"], 0.5)
        self.assertEqual(data["reliability"]["insufficiency_rate"], 0.5)
        self.assertEqual(
            data["reliability"]["freshness"],
            {"fresh": 1, "stale": 1, "unknown": 0},
        )
        self.assertEqual(
            data["usage_funnel"],
            {
                "retrieved": 2,
                "read": 2,
                "used": 1,
                "cited": 1,
                "read_rate": 1.0,
                "used_rate": 0.5,
                "cited_rate": 1.0,
            },
        )
        self.assertEqual(data["quality"]["run_id"], run_id)
        self.assertEqual(data["quality"]["holdout"]["case_count"], 2)
        self.assertEqual(data["quality"]["quality_degradation"], 0.03125)

    def test_ranks_by_risk_then_observed_impact_and_caps_nominal_path_at_seven(
        self,
    ) -> None:
        events: list[dict[str, object]] = []
        for index in range(9):
            risk = (
                ConflictRisk.HIGH
                if index < 2
                else ConflictRisk.MEDIUM
                if index < 5
                else ConflictRisk.LOW
            )
            impacts = (
                ("known_problem_avoided", "validation_command_reused")
                if index == 1
                else ("known_problem_avoided",)
                if index in {0, 2}
                else ()
            )
            events.extend(
                _debt_chain(
                    occurred_at=NOW - timedelta(hours=9 - index),
                    risk=risk,
                    impacts=impacts,
                )
            )

        outcome = build_weekly_report(
            project_id="skillz-claude",
            events=events,
            runs=[],
            quality_records=[],
            now=NOW,
        )
        data = outcome.data()

        self.assertEqual(len(data["decisions"]), 7)
        self.assertEqual(data["appendix"]["remaining_count"], 2)
        self.assertEqual(data["decisions"][0]["risk"], "high")
        self.assertEqual(data["decisions"][0]["observed_impact_count"], 2)
        self.assertEqual(data["decisions"][1]["risk"], "high")
        self.assertEqual(data["review"]["budget_minutes"], 10)
        self.assertTrue(
            data["decisions"][0]["actions"]["fix"].startswith("memory finish con_")
        )

    def test_resolved_ignored_and_future_snoozed_debts_are_not_actionable(self) -> None:
        events: list[dict[str, object]] = []
        events.extend(
            _debt_chain(
                occurred_at=NOW - timedelta(days=2),
                risk=ConflictRisk.HIGH,
                action=DebtAction.FIX,
            )
        )
        events.extend(
            _debt_chain(
                occurred_at=NOW - timedelta(days=1),
                risk=ConflictRisk.MEDIUM,
                action=DebtAction.IGNORE,
            )
        )
        events.extend(
            _debt_chain(
                occurred_at=NOW - timedelta(hours=2),
                risk=ConflictRisk.LOW,
                action=DebtAction.SNOOZE,
                snooze_until="2026-08-01",
            )
        )

        outcome = build_weekly_report(
            project_id="skillz-claude",
            events=events,
            runs=[],
            quality_records=[],
            now=NOW,
        )

        self.assertEqual(outcome.data()["decisions"], [])
        self.assertEqual(outcome.data()["review"]["budget_minutes"], 10)


if __name__ == "__main__":
    unittest.main()
