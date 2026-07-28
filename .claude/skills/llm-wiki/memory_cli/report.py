"""Pure STORY-016 weekly aggregation and debt-ranking policy."""

from __future__ import annotations

import math
import statistics
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta, timezone
from typing import Any

from .events import (
    EVENT_TYPE_CONTEXT_COMPLETED,
    EVENT_TYPE_MEMORY_CONFLICT,
    EVENT_TYPE_MEMORY_DEBT_ACTION,
    EVENT_TYPE_USAGE_ATTESTED,
)
from .receipts import WeeklyReportOutcome


WEEKLY_WINDOW_DAYS = 7
WEEKLY_DECISION_CAP = 7
WEEKLY_REVIEW_BUDGET_MINUTES = 10
_RISK_ORDER = {"high": 3, "medium": 2, "low": 1}
_NON_SUCCESS_STATUSES = {"insufficient", "blocked", "degraded"}


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("weekly report timestamps must be timezone-aware")
    return value.astimezone(timezone.utc)


def _parse_time(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("weekly report timestamps must be strings")
    normalized = f"{value[:-1]}+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    return _as_utc(parsed)


def _format_time(value: datetime) -> str:
    return _as_utc(value).isoformat(timespec="seconds").replace("+00:00", "Z")


def _rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def _distribution(values: Sequence[int]) -> dict[str, float | None]:
    if not values:
        return {"median": None, "p95": None}
    ordered = sorted(values)
    nearest_rank = max(0, math.ceil(0.95 * len(ordered)) - 1)
    return {
        "median": float(statistics.median(ordered)),
        "p95": float(ordered[nearest_rank]),
    }


def _latest_quality(
    *,
    project_id: str,
    runs: Sequence[Mapping[str, object]],
    quality_records: Sequence[Mapping[str, object]],
    period_start: datetime,
    period_end: datetime,
) -> dict[str, Any] | None:
    eligible_runs = [
        run
        for run in runs
        if run.get("project_id") == project_id
        and period_start <= _parse_time(run.get("occurred_at")) <= period_end
    ]
    if not eligible_runs:
        return None
    latest = max(eligible_runs, key=lambda run: _parse_time(run["occurred_at"]))
    run_id = latest.get("run_id")
    aggregate = latest.get("aggregate")
    if not isinstance(run_id, str) or not isinstance(aggregate, Mapping):
        return None
    quality = next(
        (
            record
            for record in quality_records
            if record.get("project_id") == project_id
            and record.get("run_id") == run_id
        ),
        None,
    )
    holdout = latest.get("holdout")
    holdout_projection: dict[str, Any] | None = None
    if isinstance(holdout, Mapping):
        holdout_aggregate = holdout.get("aggregate")
        holdout_projection = {
            "case_count": holdout.get("case_count"),
            "retrieval_hit_rate": (
                holdout_aggregate.get("retrieval_hit_rate")
                if isinstance(holdout_aggregate, Mapping)
                else None
            ),
        }
    return {
        "run_id": run_id,
        "occurred_at": latest["occurred_at"],
        "retrieval_hit_rate": aggregate.get("retrieval_hit_rate"),
        "fallback_rate": aggregate.get("fallback_rate"),
        "median_context_reduction": aggregate.get("median_context_reduction"),
        "holdout": holdout_projection,
        "rubric_version": quality.get("rubric_version") if quality else None,
        "quality_degradation": (
            quality.get("quality_degradation") if quality else None
        ),
        "reviewer_type": quality.get("reviewer_type") if quality else None,
    }


def _decision_priority(risk: str, observed_impact_count: int) -> str:
    if risk == "high":
        return "P0"
    if risk == "medium":
        return "P1"
    return "P2" if observed_impact_count else "P3"


def _action_commands(debt_id: str) -> dict[str, str]:
    prefix = f"memory finish {debt_id} --debt-action"
    return {
        "fix": f"{prefix} fix",
        "ignore": f"{prefix} ignore --reason <reason_slug>",
        "snooze": f"{prefix} snooze --until YYYY-MM-DD",
    }


def _rank_decisions(
    *,
    events: Sequence[Mapping[str, object]],
    period_start: datetime,
    period_end: datetime,
) -> tuple[tuple[dict[str, Any], ...], dict[str, Any]]:
    attestations = {
        event.get("parent_event_id"): event
        for event in events
        if event.get("event_type") == EVENT_TYPE_USAGE_ATTESTED
    }
    actions = {
        event.get("parent_event_id"): event
        for event in events
        if event.get("event_type") == EVENT_TYPE_MEMORY_DEBT_ACTION
    }
    candidates: list[dict[str, Any]] = []
    for event in events:
        if event.get("event_type") != EVENT_TYPE_MEMORY_CONFLICT:
            continue
        occurred_at = _parse_time(event.get("occurred_at"))
        if not period_start <= occurred_at <= period_end:
            continue
        payload = event.get("payload")
        if not isinstance(payload, Mapping) or payload.get("debt") is None:
            continue
        debt_id = event.get("event_id")
        if not isinstance(debt_id, str) or debt_id in actions:
            continue
        parent_id = event.get("parent_event_id")
        attestation = attestations.get(parent_id)
        attestation_payload = (
            attestation.get("payload") if isinstance(attestation, Mapping) else None
        )
        impact_codes = (
            attestation_payload.get("impact_codes", [])
            if isinstance(attestation_payload, Mapping)
            else []
        )
        observed_impact_count = len(set(impact_codes))
        risk = str(payload.get("risk"))
        memory = payload.get("memory")
        repository = payload.get("repository")
        if not isinstance(memory, Mapping) or not isinstance(repository, Mapping):
            continue
        candidates.append(
            {
                "debt_id": debt_id,
                "priority": _decision_priority(risk, observed_impact_count),
                "risk": risk,
                "category": payload.get("category"),
                "observed_impact_count": observed_impact_count,
                "memory": dict(memory),
                "repository": dict(repository),
                "actions": _action_commands(debt_id),
            }
        )
    candidates.sort(
        key=lambda item: (
            -_RISK_ORDER.get(str(item["risk"]), 0),
            -int(item["observed_impact_count"]),
            str(item["debt_id"]),
        )
    )
    nominal = tuple(candidates[:WEEKLY_DECISION_CAP])
    remaining = candidates[WEEKLY_DECISION_CAP:]
    appendix = {
        "remaining_count": len(remaining),
        "by_risk": dict(sorted(Counter(item["risk"] for item in remaining).items())),
        "by_category": dict(
            sorted(Counter(item["category"] for item in remaining).items())
        ),
    }
    return nominal, appendix


def build_weekly_report(
    *,
    project_id: str,
    events: Sequence[Mapping[str, object]],
    runs: Sequence[Mapping[str, object]],
    quality_records: Sequence[Mapping[str, object]],
    now: datetime | None = None,
    warnings: Sequence[Mapping[str, str]] = (),
) -> WeeklyReportOutcome:
    """Aggregate one project without carrying raw task material into the result."""

    period_end = _as_utc(now or datetime.now(timezone.utc))
    period_start = period_end - timedelta(days=WEEKLY_WINDOW_DAYS)
    project_events = [event for event in events if event.get("project_id") == project_id]
    weekly_events = [
        event
        for event in project_events
        if period_start <= _parse_time(event.get("occurred_at")) <= period_end
    ]
    contexts = [
        event
        for event in weekly_events
        if event.get("event_type") == EVENT_TYPE_CONTEXT_COMPLETED
    ]
    context_ids = {event.get("event_id") for event in contexts}
    attestations = [
        event
        for event in weekly_events
        if event.get("event_type") == EVENT_TYPE_USAGE_ATTESTED
        and event.get("parent_event_id") in context_ids
    ]

    tokens: list[int] = []
    durations: list[int] = []
    retrieved = read = 0
    fallback_count = insufficiency_count = activation_errors = 0
    freshness = Counter({"fresh": 0, "stale": 0, "unknown": 0})
    for event in contexts:
        payload = event["payload"]
        assert isinstance(payload, Mapping)
        token_value = payload.get("estimated_context_tokens")
        duration_value = payload.get("duration_ms")
        if isinstance(token_value, int):
            tokens.append(token_value)
        if isinstance(duration_value, int):
            durations.append(duration_value)
        retrieved += len(payload.get("retrieved", []))
        read += len(payload.get("read", []))
        if len(payload.get("route", [])) > 1:
            fallback_count += 1
        status = payload.get("status")
        if status == "insufficient":
            insufficiency_count += 1
        if status in _NON_SUCCESS_STATUSES:
            activation_errors += 1
        freshness[str(payload.get("freshness", "unknown"))] += 1

    used = cited = 0
    for event in attestations:
        payload = event["payload"]
        assert isinstance(payload, Mapping)
        used += len(payload.get("used", []))
        cited += len(payload.get("cited", []))

    decisions, appendix = _rank_decisions(
        events=project_events,
        period_start=period_start,
        period_end=period_end,
    )
    quality = _latest_quality(
        project_id=project_id,
        runs=runs,
        quality_records=quality_records,
        period_start=period_start,
        period_end=period_end,
    )
    status = (
        "ready" if contexts or quality is not None or decisions else "insufficient"
    )
    return WeeklyReportOutcome(
        status=status,
        exit_code=0 if status == "ready" else 10,
        project_id=project_id,
        period_start=_format_time(period_start),
        period_end=_format_time(period_end),
        efficiency={
            "context_events": len(contexts),
            "estimated_context_tokens": _distribution(tokens),
            "duration_ms": _distribution(durations),
        },
        quality=quality,
        reliability={
            "fallback_rate": _rate(fallback_count, len(contexts)),
            "insufficiency_rate": _rate(insufficiency_count, len(contexts)),
            "freshness": {
                "fresh": freshness["fresh"],
                "stale": freshness["stale"],
                "unknown": freshness["unknown"],
            },
            "activation_errors": activation_errors,
        },
        usage_funnel={
            "retrieved": retrieved,
            "read": read,
            "used": used,
            "cited": cited,
            "read_rate": _rate(read, retrieved),
            "used_rate": _rate(used, read),
            "cited_rate": _rate(cited, used),
        },
        decisions=decisions,
        appendix=appendix,
        review_budget_minutes=WEEKLY_REVIEW_BUDGET_MINUTES,
        warnings=tuple(dict(warning) for warning in warnings),
    )
