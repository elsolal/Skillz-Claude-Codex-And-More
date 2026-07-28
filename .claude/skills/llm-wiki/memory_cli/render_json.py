"""Stable JSON renderer for context outcomes."""

from __future__ import annotations

import json
from typing import Any, TextIO

from .contracts import PUBLIC_SCHEMA_VERSION
from .receipts import (
    ContextOutcome,
    DebtActionOutcome,
    FinishOutcome,
    GoldenTestOutcome,
    MeasurementGateOutcome,
    QualityRecordOutcome,
    WeeklyReportOutcome,
)


def context_envelope(outcome: ContextOutcome) -> dict[str, Any]:
    return {
        "schema_version": PUBLIC_SCHEMA_VERSION,
        "command": "context",
        "status": outcome.status,
        "project_id": outcome.project_id,
        "event_id": outcome.event_id,
        "data": outcome.data(),
        "warnings": list(outcome.warnings),
        "errors": list(outcome.errors),
    }


def render_context_json(outcome: ContextOutcome, *, stream: TextIO) -> None:
    print(
        json.dumps(
            context_envelope(outcome),
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        file=stream,
    )


def finish_envelope(outcome: FinishOutcome) -> dict[str, Any]:
    return {
        "schema_version": PUBLIC_SCHEMA_VERSION,
        "command": "finish",
        "status": outcome.status,
        "project_id": outcome.project_id,
        "event_id": outcome.event_id,
        "data": outcome.data(),
        "warnings": [],
        "errors": list(outcome.diagnostics),
    }


def render_finish_json(outcome: FinishOutcome, *, stream: TextIO) -> None:
    print(
        json.dumps(
            finish_envelope(outcome),
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        file=stream,
    )


def debt_action_envelope(outcome: DebtActionOutcome) -> dict[str, Any]:
    return {
        "schema_version": PUBLIC_SCHEMA_VERSION,
        "command": "finish",
        "status": outcome.status,
        "project_id": outcome.project_id,
        "event_id": outcome.event_id,
        "data": outcome.data(),
        "warnings": [],
        "errors": list(outcome.diagnostics),
    }


def render_debt_action_json(outcome: DebtActionOutcome, *, stream: TextIO) -> None:
    print(
        json.dumps(
            debt_action_envelope(outcome),
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        file=stream,
    )


def golden_test_envelope(outcome: GoldenTestOutcome) -> dict[str, Any]:
    return {
        "schema_version": PUBLIC_SCHEMA_VERSION,
        "command": "test",
        "status": outcome.status,
        "project_id": outcome.project_id,
        "run_id": outcome.run_id,
        "data": outcome.data(),
        "warnings": list(outcome.warnings),
        "errors": list(outcome.errors),
    }


def render_golden_test_json(outcome: GoldenTestOutcome, *, stream: TextIO) -> None:
    print(
        json.dumps(
            golden_test_envelope(outcome),
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        file=stream,
    )


def quality_record_envelope(outcome: QualityRecordOutcome) -> dict[str, Any]:
    return {
        "schema_version": PUBLIC_SCHEMA_VERSION,
        "command": "test.record-quality",
        "status": outcome.status,
        "project_id": outcome.project_id,
        "run_id": outcome.run_id,
        "data": outcome.data(),
        "warnings": list(outcome.warnings),
        "errors": list(outcome.errors),
    }


def render_quality_record_json(outcome: QualityRecordOutcome, *, stream: TextIO) -> None:
    print(
        json.dumps(
            quality_record_envelope(outcome),
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        file=stream,
    )


def measurement_gate_envelope(outcome: MeasurementGateOutcome) -> dict[str, Any]:
    return {
        "schema_version": PUBLIC_SCHEMA_VERSION,
        "command": "test.gate",
        "status": outcome.status,
        "project_id": outcome.project_id,
        "run_id": outcome.run_id,
        "data": outcome.data(),
        "warnings": list(outcome.warnings),
        "errors": list(outcome.errors),
    }


def render_measurement_gate_json(
    outcome: MeasurementGateOutcome,
    *,
    stream: TextIO,
) -> None:
    print(
        json.dumps(
            measurement_gate_envelope(outcome),
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        file=stream,
    )


def weekly_report_envelope(outcome: WeeklyReportOutcome) -> dict[str, Any]:
    return {
        "schema_version": PUBLIC_SCHEMA_VERSION,
        "command": "report.weekly",
        "status": outcome.status,
        "project_id": outcome.project_id,
        "data": outcome.data(),
        "warnings": list(outcome.warnings),
        "errors": list(outcome.errors),
    }


def render_weekly_report_json(
    outcome: WeeklyReportOutcome,
    *,
    stream: TextIO,
) -> None:
    print(
        json.dumps(
            weekly_report_envelope(outcome),
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        file=stream,
    )
