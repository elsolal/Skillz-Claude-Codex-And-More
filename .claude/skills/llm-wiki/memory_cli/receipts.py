"""Stable context outcomes shared by human and JSON renderers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .contracts import (
    RetrievalHit,
    RetrievalMode,
    SufficiencyDecision,
    SufficiencyReason,
    SufficiencyStatus,
    TaskCategory,
)
from .qmd_adapter import QmdSearchOutcome, QmdSearchStatus


@dataclass(frozen=True, slots=True)
class ContextOutcome:
    status: str
    exit_code: int
    project_id: str
    mode: RetrievalMode
    task_category: TaskCategory
    route: tuple[str, ...]
    retrieval_status: QmdSearchStatus
    duration_ms: int | None
    hits: tuple[RetrievalHit, ...]
    decision: SufficiencyDecision | None = None
    fallback_used: bool = False
    fallback_explicit_decision: bool = False
    fallback_reason_codes: tuple[SufficiencyReason, ...] = ()
    warnings: tuple[dict[str, Any], ...] = ()
    errors: tuple[dict[str, Any], ...] = ()

    def data(self) -> dict[str, Any]:
        retrieval: dict[str, Any] = {
            "status": self.retrieval_status.value,
            "hits": [
                {
                    "docid": hit.docid,
                    "collection": hit.collection,
                    "path": hit.relative_path.as_posix(),
                    "title": hit.title,
                    "score": hit.score,
                    "snippet_line": hit.snippet_line,
                }
                for hit in self.hits
            ],
        }
        if self.duration_ms is not None:
            retrieval["duration_ms"] = self.duration_ms
        data: dict[str, Any] = {
            "mode": self.mode.value,
            "task_category": self.task_category.value,
            "route": list(self.route),
            "retrieval": retrieval,
            "fallback": {
                "used": self.fallback_used,
                "explicit_decision": self.fallback_explicit_decision,
                "reason_codes": [reason.value for reason in self.fallback_reason_codes],
            },
        }
        if self.decision is not None:
            data["decision"] = _decision_data(self.decision)
        return data


def _decision_data(decision: SufficiencyDecision) -> dict[str, Any]:
    return {
        "status": decision.status.value,
        "thresholds_version": decision.thresholds_version,
        "reason_codes": [reason.value for reason in decision.reason_codes],
        "evidence": {
            "freshness": decision.evidence.freshness.value,
            "hits": [
                {
                    "docid": hit.docid,
                    "score": hit.score,
                    "provenance": hit.provenance.value,
                }
                for hit in decision.evidence.hits
            ],
        },
    }


def blocked_context(
    *,
    project_id: str,
    mode: RetrievalMode,
    task_category: TaskCategory,
    route: tuple[str, ...],
    retrieval_status: QmdSearchStatus,
    code: str,
    message: str,
    correction: str,
    exit_code: int,
    decision: SufficiencyDecision | None = None,
    hits: tuple[RetrievalHit, ...] = (),
    duration_ms: int | None = None,
    fallback_used: bool = False,
    fallback_explicit_decision: bool = False,
    fallback_reason_codes: tuple[SufficiencyReason, ...] = (),
) -> ContextOutcome:
    return ContextOutcome(
        status="blocked",
        exit_code=exit_code,
        project_id=project_id,
        mode=mode,
        task_category=task_category,
        route=route,
        retrieval_status=retrieval_status,
        duration_ms=duration_ms,
        hits=hits,
        decision=decision,
        fallback_used=fallback_used,
        fallback_explicit_decision=fallback_explicit_decision,
        fallback_reason_codes=fallback_reason_codes,
        errors=(
            {
                "code": code,
                "message": message,
                "correction": correction,
            },
        ),
    )


def context_outcome(
    *,
    project_id: str,
    mode: RetrievalMode,
    task_category: TaskCategory,
    route: tuple[str, ...],
    retrieval: QmdSearchOutcome,
    hits: tuple[RetrievalHit, ...],
    duration_ms: int,
    decision: SufficiencyDecision,
    fallback_used: bool = False,
    fallback_explicit_decision: bool = False,
    fallback_reason_codes: tuple[SufficiencyReason, ...] = (),
    warnings: tuple[dict[str, Any], ...] = (),
) -> ContextOutcome:
    exit_code = {
        SufficiencyStatus.SUFFICIENT: 0,
        SufficiencyStatus.INSUFFICIENT: 20,
        SufficiencyStatus.AMBIGUOUS: 21,
        SufficiencyStatus.BLOCKED: 33,
    }[decision.status]
    return ContextOutcome(
        status=decision.status.value,
        exit_code=exit_code,
        project_id=project_id,
        mode=mode,
        task_category=task_category,
        route=route,
        retrieval_status=retrieval.status,
        duration_ms=duration_ms,
        hits=hits,
        decision=decision,
        fallback_used=fallback_used,
        fallback_explicit_decision=fallback_explicit_decision,
        fallback_reason_codes=fallback_reason_codes,
        warnings=warnings,
    )
