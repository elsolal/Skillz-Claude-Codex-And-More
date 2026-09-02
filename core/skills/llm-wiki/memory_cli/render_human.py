"""Plain-text renderers for context receipts."""

from __future__ import annotations

from typing import TextIO

from .receipts import (
    ContextInitialReceipt,
    ContextOutcome,
    DebtActionOutcome,
    FinishOutcome,
    GoldenTestOutcome,
    MeasurementGateOutcome,
    QualityRecordOutcome,
    WeeklyReportOutcome,
)


def render_context_initial(receipt: ContextInitialReceipt, *, stream: TextIO) -> None:
    route = " -> ".join(receipt.planned_route)
    if len(receipt.planned_route) > 1:
        route += " in declared trust/policy order"
    print(f"Memory · {receipt.mode.value.upper()} · {receipt.project_id}", file=stream)
    print(f"Route: {route}", file=stream)
    print(
        f"Budget: {receipt.target_tokens:,} estimated tokens · "
        f"hard cap {receipt.hard_tokens:,} · task: {receipt.task_category.value}",
        file=stream,
    )
    print("Status: retrieving project context", file=stream)


def render_context_final(
    outcome: ContextOutcome,
    *,
    explain: bool,
    stream: TextIO,
) -> None:
    final = outcome.final_receipt_data()
    route_label = "fallback used" if outcome.fallback_used else "project-only"
    event_label = outcome.event_id or "not recorded"
    duration = (
        f"{final['duration_ms']}ms"
        if final["duration_ms"] is not None
        else "duration unavailable"
    )
    budget = final["budget_tokens"] if final["budget_tokens"] is not None else 0

    print(
        f"Memory {outcome.status} · {route_label} · event {event_label}",
        file=stream,
    )
    print(
        f"Measured: {final['retrieved']} retrieved · {final['read']} read · "
        f"~{final['estimated_tokens']}/{budget} tokens · {duration}",
        file=stream,
    )
    print(f"Freshness: {final['freshness']}", file=stream)
    fallback_label = "used" if outcome.fallback_used else "not used"
    print(f"Fallback: {fallback_label}", file=stream)

    if explain and outcome.decision is not None:
        reasons = ", ".join(
            reason.value for reason in outcome.decision.reason_codes
        )
        print(f"Reason codes: {reasons or 'none'}", file=stream)
        print(
            "Decision: "
            f"{outcome.decision.status.value} · "
            f"thresholds {outcome.decision.thresholds_version}",
            file=stream,
        )
        for hit in outcome.decision.evidence.hits:
            print(
                f"  {hit.docid} · score {hit.score:g} · "
                f"provenance {hit.provenance.value} · trust {hit.trust.value}",
                file=stream,
            )
        if outcome.fallback_explicit_decision:
            print("Fallback decision: explicit", file=stream)
        fallback_reasons = ", ".join(
            reason.value for reason in outcome.fallback_reason_codes
        )
        if fallback_reasons:
            print(f"Fallback reason codes: {fallback_reasons}", file=stream)

    if outcome.assembly is not None:
        assembly = outcome.assembly
        source = f" · source {assembly.source}"
        page_limit = (
            f" · cap {assembly.page_limit} page(s)"
            if assembly.page_limit is not None
            else ""
        )
        print(
            f"Context: {len(assembly.sections)} section(s){source}{page_limit}",
            file=stream,
        )
        if assembly.hard_cap_exceeded:
            print(
                f"Hard cap exceeded: {assembly.hard_tokens} · "
                f"risk reason {assembly.risk_reason.value}",
                file=stream,
            )
        for section in assembly.sections:
            print(
                f"\n[{section.docid}] {section.relative_path.as_posix()} "
                f"· lines {section.line_start}-{section.line_end} "
                f"· {section.estimated_tokens} tokens · trust {section.trust.value}",
                file=stream,
            )
            print(section.content.rstrip(), file=stream)

    for warning in outcome.warnings:
        print(f"Warning: {warning['message']}", file=stream)
        print(f"Correction: {warning['correction']}", file=stream)
    for error in outcome.errors:
        print(f"Error: {error['message']}", file=stream)
        print(f"Correction: {error['correction']}", file=stream)
    print("Machine output: memory context --json", file=stream)


def render_finish_human(outcome: FinishOutcome, *, stream: TextIO) -> None:
    measured = outcome.measured_data()
    attested = outcome.attested_data()
    duration = (
        f"{measured['duration_ms']}ms"
        if measured["duration_ms"] is not None
        else "duration unavailable"
    )
    impact = (
        " · ".join(code.replace("_", " ") for code in attested["impact_codes"])
        or "none observed"
    )

    print(f"Memory final · event {outcome.event_id}", file=stream)
    print(
        f"Measured: {measured['retrieved']} retrieved · {measured['read']} read · "
        f"~{measured['estimated_tokens']}/{measured['budget_tokens']} tokens · {duration}",
        file=stream,
    )
    print(
        f"Attested: {len(attested['used'])} used · {len(attested['cited'])} cited",
        file=stream,
    )
    print(f"Impact: {impact}", file=stream)
    if outcome.conflict_event is not None:
        conflict = outcome.conflict_data()
        print(file=stream)
        print(
            f"Memory conflict · {str(conflict['risk']).upper()} RISK",
            file=stream,
        )
        print(
            f"Memory: {conflict['memory']['docid']} · {conflict['memory']['path']}",
            file=stream,
        )
        print(
            "Repository: "
            f"{conflict['repository']['path']} · "
            f"{conflict['repository']['evidence_type']} · "
            f"trust {conflict['repository']['trust']}",
            file=stream,
        )
        print("Decision: repository evidence takes precedence", file=stream)
        human = "yes" if conflict["requires_human"] else "no"
        print(f"Human arbitration: {human}", file=stream)
        if conflict["debt"] is not None:
            print(
                f"Debt: {conflict['debt']['id']} · open metadata-only draft",
                file=stream,
            )
        action_labels = {
            "continue": "[c] continue with repository evidence",
            "inspect": "[i] inspect both sources",
            "prepare_patch": "[p] prepare a source-backed memory patch",
        }
        print("Actions:", file=stream)
        for action in conflict["next_actions"]:
            print(f"  {action_labels[action]}", file=stream)
    for diagnostic in outcome.diagnostics:
        print(f"Error: {diagnostic['message']}", file=stream)
        print(f"Correction: {diagnostic['correction']}", file=stream)
    print("Machine output: memory finish --json", file=stream)


def render_golden_test_human(
    outcome: GoldenTestOutcome,
    *,
    stream: TextIO,
) -> None:
    aggregate = outcome.aggregate
    print(f"Memory test {outcome.status} · run {outcome.run_id}", file=stream)
    print(f"Cases: {len(outcome.cases) + outcome.holdout_case_count}", file=stream)
    if outcome.holdout_case_count:
        print(
            f"Holdout: {outcome.holdout_case_count} local case(s) · aggregate only",
            file=stream,
        )
    print(
        f"Retrieval hit rate: {aggregate['retrieval_hit_rate']:.1%}",
        file=stream,
    )
    print(f"Fallback rate: {aggregate['fallback_rate']:.1%}", file=stream)
    print(
        "Median context reduction: "
        f"{aggregate['median_context_reduction']:.1%}",
        file=stream,
    )
    print(f"Estimator: {outcome.estimator_version}", file=stream)
    for error in outcome.errors:
        print(f"Error: {error['message']}", file=stream)
        print(f"Correction: {error['correction']}", file=stream)
    print("Machine output: memory test --json", file=stream)


def render_quality_record_human(
    outcome: QualityRecordOutcome,
    *,
    stream: TextIO,
) -> None:
    print(f"Memory quality {outcome.status} · run {outcome.run_id}", file=stream)
    print(f"Rubric: {outcome.rubric_version}", file=stream)
    print(f"Reviewer: {outcome.reviewer_type}", file=stream)
    print(f"Baseline score: {outcome.baseline_score:g}", file=stream)
    print(f"Bounded score: {outcome.score:g}", file=stream)
    print(f"Quality degradation: {outcome.quality_degradation:.1%}", file=stream)
    print("Raw response stored: no", file=stream)
    for error in outcome.errors:
        print(f"Error: {error['message']}", file=stream)
        print(f"Correction: {error['correction']}", file=stream)
    print("Machine output: memory test record-quality --json", file=stream)


def render_measurement_gate_human(
    outcome: MeasurementGateOutcome,
    *,
    stream: TextIO,
) -> None:
    gate = outcome.gate
    print(f"Memory measurement gate {outcome.status.upper()} · run {outcome.run_id}", file=stream)
    for name, dimension in gate["dimensions"].items():
        print(f"{name.capitalize()}: {dimension['status']} · {dimension['value']}", file=stream)
    print("Global rollout authorized: no", file=stream)
    print("Machine output: memory test gate --json", file=stream)


def render_debt_action_human(
    outcome: DebtActionOutcome, *, stream: TextIO
) -> None:
    action = outcome.action_data()
    print(f"Memory debt · {outcome.debt_id}", file=stream)
    print(f"Action: {action['action']}", file=stream)
    if action["reason"] is not None:
        print(f"Reason: {action['reason']}", file=stream)
    if action["snooze_until"] is not None:
        print(f"Snooze until: {action['snooze_until']}", file=stream)
    print(f"Event: {outcome.event_id}", file=stream)
    print("Shared memory: unchanged", file=stream)
    for diagnostic in outcome.diagnostics:
        print(f"Error: {diagnostic['message']}", file=stream)
        print(f"Correction: {diagnostic['correction']}", file=stream)
    print("Machine output: memory finish --json", file=stream)


def _metric(value: object) -> str:
    return "not available" if value is None else f"{value:g}"


def _terminal_text(value: object) -> str:
    return "".join(
        character if character.isprintable() else "?" for character in str(value)
    )


def render_weekly_report_human(
    outcome: WeeklyReportOutcome,
    *,
    stream: TextIO,
) -> None:
    data = outcome.data()
    review = data["review"]
    efficiency = data["efficiency"]
    reliability = data["reliability"]
    funnel = data["usage_funnel"]
    decision_label = "decision" if review["decision_count"] == 1 else "decisions"
    print(f"Memory Weekly · {outcome.project_id} · {outcome.period_end[:10]}", file=stream)
    print("Scope: local detail + shareable project aggregates", file=stream)
    print(
        f"Review budget: {review['budget_minutes']} minutes · "
        f"{review['decision_count']} {decision_label}",
        file=stream,
    )
    print(file=stream)
    print(
        "Efficiency: "
        f"{efficiency['context_events']} context event(s) · "
        f"tokens median {_metric(efficiency['estimated_context_tokens']['median'])} "
        f"p95 {_metric(efficiency['estimated_context_tokens']['p95'])} · "
        f"duration median {_metric(efficiency['duration_ms']['median'])}ms "
        f"p95 {_metric(efficiency['duration_ms']['p95'])}ms",
        file=stream,
    )
    quality = data["quality"]
    if quality is None:
        print("Quality: not measured this week", file=stream)
    else:
        degradation = quality["quality_degradation"]
        quality_label = (
            "not imported" if degradation is None else f"{degradation:.1%} degradation"
        )
        print(
            f"Quality: {quality['retrieval_hit_rate']:.1%} retrieval · {quality_label}",
            file=stream,
        )
    print(
        f"Reliability: {reliability['fallback_rate']:.1%} fallback · "
        f"{reliability['insufficiency_rate']:.1%} insufficient · "
        f"{reliability['freshness']['stale']} stale",
        file=stream,
    )
    print(
        f"Funnel: {funnel['retrieved']} retrieved -> {funnel['read']} read -> "
        f"{funnel['used']} used -> {funnel['cited']} cited",
        file=stream,
    )
    print(file=stream)
    if not outcome.decisions:
        print("Healthy · no human decision required this week", file=stream)
    else:
        print("Decisions", file=stream)
        for index, decision in enumerate(outcome.decisions, start=1):
            print(
                f"{index}. {decision['priority']} · "
                f"{str(decision['risk']).upper()} · {decision['category']} · "
                f"{decision['memory']['docid']} · "
                f"{decision['observed_impact_count']} observed impact(s)",
                file=stream,
            )
            print(f"   {_terminal_text(decision['memory']['path'])}", file=stream)
            for action in ("fix", "ignore", "snooze"):
                print(f"   {_terminal_text(decision['actions'][action])}", file=stream)
    if outcome.appendix["remaining_count"]:
        print(file=stream)
        print(
            f"Appendix: {outcome.appendix['remaining_count']} additional debt(s) · "
            f"by risk {outcome.appendix['by_risk']}",
            file=stream,
        )
    print(file=stream)
    print("Privacy: 0 prompts · 0 responses · 0 cross-project raw events", file=stream)
    for warning in outcome.warnings:
        print(f"Warning: {warning['message']}", file=stream)
        print(f"Correction: {warning['correction']}", file=stream)
    for error in outcome.errors:
        print(f"Error: {error['message']}", file=stream)
        print(f"Correction: {error['correction']}", file=stream)
    print("Machine output: memory report --weekly --json", file=stream)
