"""Plain-text renderers for context receipts."""

from __future__ import annotations

from typing import TextIO

from .receipts import ContextInitialReceipt, ContextOutcome, FinishOutcome


def render_context_initial(receipt: ContextInitialReceipt, *, stream: TextIO) -> None:
    route = " -> ".join(receipt.planned_route)
    if len(receipt.planned_route) > 1:
        route += " if insufficient and authorized"
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
                f"provenance {hit.provenance.value}",
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
                f"· {section.estimated_tokens} tokens",
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
    print("Machine output: memory finish --json", file=stream)
