"""Stable context outcomes shared by human and JSON renderers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .contracts import (
    AssemblyStatus,
    ContextAssembly,
    RetrievalHit,
    RetrievalMode,
    SufficiencyDecision,
    SufficiencyReason,
    SufficiencyStatus,
    TaskCategory,
)
from .qmd_adapter import QmdSearchOutcome, QmdSearchStatus
from .tokens import ESTIMATOR_VERSION


@dataclass(frozen=True, slots=True)
class ContextInitialReceipt:
    """Route and budget known before retrieval starts; never contains the query."""

    project_id: str
    mode: RetrievalMode
    task_category: TaskCategory
    planned_route: tuple[str, ...]
    target_tokens: int
    hard_tokens: int

    def data(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "mode": self.mode.value,
            "task_category": self.task_category.value,
            "planned_route": list(self.planned_route),
            "budget": {
                "target_tokens": self.target_tokens,
                "hard_tokens": self.hard_tokens,
            },
            "status": "retrieving",
        }


@dataclass(frozen=True, slots=True)
class FinishOutcome:
    """Consolidated view over immutable measured and attested events."""

    project_id: str
    parent_event: dict[str, Any]
    attestation_event: dict[str, Any]

    @property
    def event_id(self) -> str:
        return str(self.attestation_event["event_id"])

    @property
    def parent_event_id(self) -> str:
        return str(self.parent_event["event_id"])

    def measured_data(self) -> dict[str, Any]:
        payload = self.parent_event["payload"]
        return {
            "status": payload["status"],
            "retrieved": len(payload["retrieved"]),
            "read": len(payload["read"]),
            "estimated_tokens": payload["estimated_context_tokens"],
            "budget_tokens": payload["budget_tokens"],
            "duration_ms": payload["duration_ms"],
            "freshness": payload["freshness"],
            "fallback": {
                "used": bool(payload["fallback_reason_codes"]),
                "reason_codes": list(payload["fallback_reason_codes"]),
            },
        }

    def attested_data(self) -> dict[str, Any]:
        payload = self.attestation_event["payload"]
        return {
            "impact_taxonomy_version": payload["impact_taxonomy_version"],
            "used": list(payload["used"]),
            "cited": list(payload["cited"]),
            "citation_only": list(payload["citation_only"]),
            "impact_codes": list(payload["impact_codes"]),
        }

    def data(self) -> dict[str, Any]:
        return {
            "parent_event_id": self.parent_event_id,
            "measured": self.measured_data(),
            "attested": self.attested_data(),
        }


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
    initial_receipt: ContextInitialReceipt
    decision: SufficiencyDecision | None = None
    fallback_used: bool = False
    fallback_explicit_decision: bool = False
    fallback_reason_codes: tuple[SufficiencyReason, ...] = ()
    warnings: tuple[dict[str, Any], ...] = ()
    errors: tuple[dict[str, Any], ...] = ()
    assembly: ContextAssembly | None = None
    event_id: str | None = None

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
        if self.assembly is not None:
            metadata = self.assembly.receipt_metadata()
            data["context"] = {
                "status": metadata["status"],
                "source": metadata["source"],
                "page_limit": metadata["page_limit"],
                "estimator_version": metadata["estimator_version"],
                "budget": {
                    "target_tokens": metadata["target_tokens"],
                    "hard_tokens": metadata["hard_tokens"],
                },
                "estimated_tokens": metadata["estimated_tokens"],
                "remaining_target_tokens": metadata["remaining_target_tokens"],
                "retrieved_count": metadata["retrieved_count"],
                "read_count": metadata["read_count"],
                "hard_cap_exceeded": metadata["hard_cap_exceeded"],
                "risk_reason": metadata["risk_reason"],
                "reason_codes": metadata["reason_codes"],
                "sections": [
                    {
                        "docid": section.docid,
                        "collection": section.collection,
                        "path": section.relative_path.as_posix(),
                        "title": section.title,
                        "provenance": section.provenance.value,
                        "line_start": section.line_start,
                        "line_end": section.line_end,
                        "frontmatter": dict(section.frontmatter),
                        "estimated_tokens": section.estimated_tokens,
                        "truncated": section.truncated,
                        "content": section.content,
                    }
                    for section in self.assembly.sections
                ],
            }
        data["receipt"] = {
            "initial": self.initial_receipt.data(),
            "final": self.final_receipt_data(),
        }
        return data

    def final_receipt_data(self) -> dict[str, Any]:
        assembly = self.assembly
        retrieved = len(assembly.retrieved) if assembly is not None else len(self.hits)
        read = len(assembly.sections) if assembly is not None else 0
        estimated_tokens = assembly.estimated_tokens if assembly is not None else 0
        budget_tokens = self.initial_receipt.target_tokens
        freshness = (
            self.decision.evidence.freshness.value
            if self.decision is not None
            else "unknown"
        )
        return {
            "status": self.status,
            "retrieved": retrieved,
            "read": read,
            "estimated_tokens": estimated_tokens,
            "budget_tokens": budget_tokens,
            "duration_ms": self.duration_ms,
            "freshness": freshness,
            "fallback": {
                "used": self.fallback_used,
                "reason_codes": [
                    reason.value for reason in self.fallback_reason_codes
                ],
            },
        }

    def event_metadata(self) -> dict[str, Any]:
        """Project every completed retrieval onto the closed event V1 contract."""

        if self.assembly is not None:
            measured = self.assembly.event_metadata()
        else:
            measured = {
                "retrieved": [
                    {
                        "docid": hit.docid,
                        "collection": hit.collection,
                        "path": hit.relative_path.as_posix(),
                        "score": hit.score,
                    }
                    for hit in self.hits
                ],
                "read": [],
                "estimated_context_tokens": 0,
                "estimator_version": ESTIMATOR_VERSION,
                "budget_tokens": self.initial_receipt.target_tokens,
                "risk_reason": None,
            }
        return {
            "project_id": self.project_id,
            "mode": self.mode.value,
            "task_category": self.task_category.value,
            "status": self.status,
            "route": list(self.route),
            "retrieved": measured["retrieved"],
            "read": measured["read"],
            "estimated_context_tokens": measured["estimated_context_tokens"],
            "estimator_version": measured["estimator_version"],
            "budget_tokens": measured["budget_tokens"],
            "duration_ms": self.duration_ms,
            "freshness": (
                self.decision.evidence.freshness.value if self.decision else "unknown"
            ),
            "fallback_reason_codes": [
                reason.value for reason in self.fallback_reason_codes
            ],
            "risk_reason": measured["risk_reason"],
        }


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
    initial_receipt: ContextInitialReceipt,
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
        initial_receipt=initial_receipt,
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


def degraded_context(
    *,
    project_id: str,
    mode: RetrievalMode,
    task_category: TaskCategory,
    route: tuple[str, ...],
    retrieval_status: QmdSearchStatus,
    code: str,
    message: str,
    correction: str,
    assembly: ContextAssembly,
    initial_receipt: ContextInitialReceipt,
    hits: tuple[RetrievalHit, ...] = (),
    duration_ms: int | None = None,
    fallback_used: bool = False,
    fallback_explicit_decision: bool = False,
    fallback_reason_codes: tuple[SufficiencyReason, ...] = (),
    warnings: tuple[dict[str, Any], ...] = (),
) -> ContextOutcome:
    """Return usable bounded local context while exposing reduced coverage."""

    return ContextOutcome(
        status="degraded",
        exit_code=10,
        project_id=project_id,
        mode=mode,
        task_category=task_category,
        route=route,
        retrieval_status=retrieval_status,
        duration_ms=duration_ms,
        hits=hits,
        initial_receipt=initial_receipt,
        fallback_used=fallback_used,
        fallback_explicit_decision=fallback_explicit_decision,
        fallback_reason_codes=fallback_reason_codes,
        warnings=(
            {
                "code": code,
                "message": message,
                "correction": correction,
            },
            *warnings,
        ),
        assembly=assembly,
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
    initial_receipt: ContextInitialReceipt,
    fallback_used: bool = False,
    fallback_explicit_decision: bool = False,
    fallback_reason_codes: tuple[SufficiencyReason, ...] = (),
    warnings: tuple[dict[str, Any], ...] = (),
    assembly: ContextAssembly | None = None,
) -> ContextOutcome:
    if assembly is not None and assembly.status is not AssemblyStatus.READY:
        status = "insufficient"
        exit_code = 20
    else:
        status = decision.status.value
        exit_code = {
            SufficiencyStatus.SUFFICIENT: 0,
            SufficiencyStatus.INSUFFICIENT: 20,
            SufficiencyStatus.AMBIGUOUS: 21,
            SufficiencyStatus.BLOCKED: 33,
        }[decision.status]
    effective_hits = assembly.retrieved if assembly is not None else hits
    return ContextOutcome(
        status=status,
        exit_code=exit_code,
        project_id=project_id,
        mode=mode,
        task_category=task_category,
        route=route,
        retrieval_status=(QmdSearchStatus.READY if effective_hits else retrieval.status),
        duration_ms=duration_ms,
        hits=effective_hits,
        initial_receipt=initial_receipt,
        decision=decision,
        fallback_used=fallback_used,
        fallback_explicit_decision=fallback_explicit_decision,
        fallback_reason_codes=fallback_reason_codes,
        warnings=warnings,
        assembly=assembly,
    )
