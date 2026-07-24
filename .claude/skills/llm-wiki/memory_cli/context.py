"""Project-first retrieval, sufficiency evaluation and authorized fallback."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .assembly import DocumentAccessError, assemble_context, assemble_entry_pages
from .contracts import (
    FreshnessStatus,
    MemoryManifest,
    MemoryProjection,
    RetrievalHit,
    RetrievalMode,
    RiskReason,
    SufficiencyEvidence,
    SufficiencyDecision,
    SufficiencyHit,
    SufficiencyReason,
    SufficiencyStatus,
    TaskCategory,
)
from .freshness import collection_freshness
from .manifest import discover_manifest, load_manifest
from .projection import load_projection
from .qmd_adapter import (
    DEFAULT_SEARCH_TIMEOUT_SECONDS,
    QmdInvocationError,
    QmdOutputError,
    QmdSearchOutcome,
    QmdSearchStatus,
    QmdTimeoutError,
    Runner,
    inspect_qmd,
    search_qmd,
)
from .receipts import ContextOutcome, blocked_context, context_outcome, degraded_context
from .routing import authorized_fallbacks
from .sufficiency import evaluate_sufficiency, provenance_for_path, thresholds_for


MODE_SEARCH_LIMITS: dict[RetrievalMode, int] = {
    RetrievalMode.MINIMAL: 3,
    RetrievalMode.PROJECT: 8,
    RetrievalMode.HISTORICAL: 15,
}
QMD_INSTALL_COMMAND = "bun install -g @tobilu/qmd"


def _qmd_executable() -> str | None:
    override = os.environ.get("SKILLZ_MEMORY_QMD")
    if override is None:
        return shutil.which("qmd")
    candidate = Path(override)
    if not candidate.is_file() or not os.access(candidate, os.X_OK):
        return None
    return override


def _search(
    executable: str,
    *,
    query: str,
    collection: str,
    mode: RetrievalMode,
    thresholds_version: str,
    runner: Runner,
    timeout_seconds: float,
) -> QmdSearchOutcome:
    return search_qmd(
        executable,
        query=query,
        collection=collection,
        limit=MODE_SEARCH_LIMITS[mode],
        min_score=thresholds_for(thresholds_version, mode).candidate_score,
        runner=runner,
        timeout_seconds=timeout_seconds,
    )


def _evidence(
    *,
    mode: RetrievalMode,
    task_category: TaskCategory,
    hits: tuple[RetrievalHit, ...],
    freshness: FreshnessStatus,
    thresholds_version: str,
) -> SufficiencyEvidence:
    return SufficiencyEvidence(
        mode=mode,
        task_category=task_category,
        hits=tuple(
            SufficiencyHit(
                docid=hit.docid,
                score=hit.score,
                provenance=provenance_for_path(hit.relative_path),
            )
            for hit in hits
        ),
        freshness=freshness,
        thresholds_version=thresholds_version,
    )

def _search_failure_details(
    error: Exception,
) -> tuple[QmdSearchStatus, str, str, str, int]:
    if isinstance(error, QmdTimeoutError):
        return (
            QmdSearchStatus.TIMEOUT,
            "qmd_timeout",
            "The QMD search exceeded its bounded timeout.",
            "Retry memory context or run memory doctor.",
            40,
        )
    if isinstance(error, QmdOutputError):
        retrieval_status = QmdSearchStatus.INVALID
        code = "qmd_invalid_output"
        message = "The QMD search returned an unsupported result."
        correction = "Repair or update QMD 0.9.x, then run memory doctor."
    else:
        retrieval_status = QmdSearchStatus.ERROR
        code = "qmd_search_failed"
        message = "The QMD search failed."
        correction = "Run memory doctor, then retry the context command."
    return retrieval_status, code, message, correction, 40


def _search_failure(
    error: Exception,
    *,
    project_id: str,
    mode: RetrievalMode,
    task_category: TaskCategory,
    route: tuple[str, ...],
    hits: tuple[RetrievalHit, ...] = (),
    duration_ms: int | None = None,
    fallback_reason_codes: tuple[SufficiencyReason, ...] = (),
    explicit_decision: bool = False,
) -> ContextOutcome:
    retrieval_status, code, message, correction, exit_code = _search_failure_details(error)
    return blocked_context(
        project_id=project_id,
        mode=mode,
        task_category=task_category,
        route=route,
        retrieval_status=retrieval_status,
        code=code,
        message=message,
        correction=correction,
        exit_code=exit_code,
        hits=hits,
        duration_ms=duration_ms,
        fallback_used=len(route) > 1,
        fallback_explicit_decision=explicit_decision,
        fallback_reason_codes=fallback_reason_codes,
    )


def _local_entry_page_fallback(
    *,
    manifest: MemoryManifest,
    projection: MemoryProjection,
    mode: RetrievalMode,
    task_category: TaskCategory,
    route: tuple[str, ...],
    retrieval_status: QmdSearchStatus,
    code: str,
    message: str,
    correction: str,
    duration_ms: int | None = None,
) -> ContextOutcome:
    if mode is RetrievalMode.HISTORICAL:
        return blocked_context(
            project_id=manifest.project.id,
            mode=mode,
            task_category=task_category,
            route=route,
            retrieval_status=retrieval_status,
            code=code,
            message=message,
            correction=correction,
            exit_code=31,
            duration_ms=duration_ms,
        )

    assembly, issues = assemble_entry_pages(
        manifest.stores.project.entry_pages,
        mode=mode,
        budget=manifest.budgets[mode],
        root=projection.stores["project"].root,
    )
    if not assembly.sections:
        return blocked_context(
            project_id=manifest.project.id,
            mode=mode,
            task_category=task_category,
            route=route,
            retrieval_status=retrieval_status,
            code="entry_pages_unavailable",
            message="QMD is unavailable and no bounded project entry page can be read.",
            correction=(
                "Restore a declared entry page or repair QMD, then retry memory context."
            ),
            exit_code=32,
            duration_ms=duration_ms,
        )

    return degraded_context(
        project_id=manifest.project.id,
        mode=mode,
        task_category=task_category,
        route=route,
        retrieval_status=retrieval_status,
        code=code,
        message=message,
        correction=correction,
        duration_ms=duration_ms,
        assembly=assembly,
        warnings=tuple(
            {
                "code": issue.code,
                "path": issue.relative_path.as_posix(),
                "message": issue.message,
                "correction": issue.correction,
            }
            for issue in issues
        ),
    )


def _materialize_context(
    *,
    manifest: MemoryManifest,
    projection: MemoryProjection,
    mode: RetrievalMode,
    task_category: TaskCategory,
    route: tuple[str, ...],
    retrieval: QmdSearchOutcome,
    hits: tuple[RetrievalHit, ...],
    duration_ms: int,
    decision: SufficiencyDecision,
    risk_reason: RiskReason | None,
    fallback_used: bool = False,
    fallback_explicit_decision: bool = False,
    fallback_reason_codes: tuple[SufficiencyReason, ...] = (),
    warnings: tuple[dict[str, Any], ...] = (),
) -> ContextOutcome:
    project_collection = manifest.stores.project.collection
    collection_roots = {
        project_collection: projection.stores["project"].root,
    }
    for fallback in manifest.fallbacks:
        local_store = projection.stores.get(fallback.id)
        if fallback.collection in route and local_store is not None:
            collection_roots[fallback.collection] = local_store.root
    try:
        assembly = assemble_context(
            hits,
            mode=mode,
            task_category=task_category,
            freshness=decision.evidence.freshness,
            thresholds_version=decision.thresholds_version,
            budget=manifest.budgets[mode],
            collection_roots=collection_roots,
            risk_reason=risk_reason,
        )
    except DocumentAccessError as error:
        return blocked_context(
            project_id=manifest.project.id,
            mode=mode,
            task_category=task_category,
            route=route,
            retrieval_status=QmdSearchStatus.READY,
            code=error.code,
            message=error.message,
            correction=error.correction,
            exit_code=error.exit_code,
            decision=decision,
            hits=hits,
            duration_ms=duration_ms,
            fallback_used=fallback_used,
            fallback_explicit_decision=fallback_explicit_decision,
            fallback_reason_codes=fallback_reason_codes,
        )
    return context_outcome(
        project_id=manifest.project.id,
        mode=mode,
        task_category=task_category,
        route=route,
        retrieval=retrieval,
        hits=hits,
        duration_ms=duration_ms,
        decision=decision,
        fallback_used=fallback_used,
        fallback_explicit_decision=fallback_explicit_decision,
        fallback_reason_codes=fallback_reason_codes,
        warnings=warnings,
        assembly=assembly,
    )


def run_context(
    *,
    mode: RetrievalMode,
    task_category: TaskCategory,
    query: str,
    fallback_on_ambiguous: bool = False,
    risk_reason: RiskReason | None = None,
    runner: Runner = subprocess.run,
    timeout_seconds: float = DEFAULT_SEARCH_TIMEOUT_SECONDS,
) -> ContextOutcome:
    """Search project first, stop when sufficient, and authorize any fallback."""

    manifest_path = discover_manifest()
    manifest = load_manifest(manifest_path)
    projection = load_projection(manifest_path)
    project_collection = manifest.stores.project.collection
    route = (project_collection,)
    executable = _qmd_executable()
    if executable is None:
        return _local_entry_page_fallback(
            manifest=manifest,
            projection=projection,
            mode=mode,
            task_category=task_category,
            route=route,
            retrieval_status=QmdSearchStatus.ERROR,
            code="qmd_missing",
            message="QMD is required for project retrieval but is unavailable.",
            correction=QMD_INSTALL_COMMAND,
        )

    try:
        project_retrieval = _search(
            executable,
            query=query,
            collection=project_collection,
            mode=mode,
            thresholds_version=manifest.policy.sufficiency_thresholds_version,
            runner=runner,
            timeout_seconds=timeout_seconds,
        )
    except (QmdTimeoutError, QmdOutputError, QmdInvocationError) as error:
        retrieval_status, code, message, correction, _ = _search_failure_details(error)
        return _local_entry_page_fallback(
            manifest=manifest,
            projection=projection,
            mode=mode,
            task_category=task_category,
            route=route,
            retrieval_status=retrieval_status,
            code=code,
            message=message,
            correction=correction,
        )

    try:
        qmd_status = inspect_qmd(
            executable,
            runner=runner,
            timeout_seconds=timeout_seconds,
        )
        collections = qmd_status.collections
    except (QmdTimeoutError, QmdOutputError, QmdInvocationError):
        collections = {}

    project_decision = evaluate_sufficiency(
        _evidence(
            mode=mode,
            task_category=task_category,
            hits=project_retrieval.hits,
            freshness=collection_freshness(collections.get(project_collection)),
            thresholds_version=manifest.policy.sufficiency_thresholds_version,
        )
    )
    if project_decision.status is SufficiencyStatus.SUFFICIENT:
        return _materialize_context(
            manifest=manifest,
            projection=projection,
            mode=mode,
            task_category=task_category,
            route=route,
            retrieval=project_retrieval,
            hits=project_retrieval.hits,
            duration_ms=project_retrieval.duration_ms,
            decision=project_decision,
            risk_reason=risk_reason,
            warnings=(
                (
                    {
                        "code": "qmd_index_stale",
                        "message": "The project QMD collection is stale.",
                        "correction": "qmd update && qmd embed",
                    },
                )
                if SufficiencyReason.STALE in project_decision.reason_codes
                else ()
            ),
        )

    if (
        project_decision.status is SufficiencyStatus.AMBIGUOUS
        and not fallback_on_ambiguous
    ):
        return context_outcome(
            project_id=manifest.project.id,
            mode=mode,
            task_category=task_category,
            route=route,
            retrieval=project_retrieval,
            hits=project_retrieval.hits,
            duration_ms=project_retrieval.duration_ms,
            decision=project_decision,
        )

    fallbacks = authorized_fallbacks(
        manifest,
        principal_role=projection.principal_role,
        task_category=task_category,
    )
    if not fallbacks:
        return context_outcome(
            project_id=manifest.project.id,
            mode=mode,
            task_category=task_category,
            route=route,
            retrieval=project_retrieval,
            hits=project_retrieval.hits,
            duration_ms=project_retrieval.duration_ms,
            decision=project_decision,
            warnings=(
                {
                    "code": "fallback_not_authorized",
                    "message": (
                        "No transverse fallback is authorized for this local role "
                        "and task category."
                    ),
                    "correction": (
                        "Continue project-only or update the shared manifest policy "
                        "through review."
                    ),
                },
            ),
        )

    fallback = fallbacks[0]
    route = (project_collection, fallback.collection)
    explicit_decision = project_decision.status is SufficiencyStatus.AMBIGUOUS
    try:
        fallback_retrieval = _search(
            executable,
            query=query,
            collection=fallback.collection,
            mode=mode,
            thresholds_version=manifest.policy.sufficiency_thresholds_version,
            runner=runner,
            timeout_seconds=timeout_seconds,
        )
    except (QmdTimeoutError, QmdOutputError, QmdInvocationError) as error:
        return _search_failure(
            error,
            project_id=manifest.project.id,
            mode=mode,
            task_category=task_category,
            route=route,
            hits=project_retrieval.hits,
            duration_ms=project_retrieval.duration_ms,
            fallback_reason_codes=project_decision.reason_codes,
            explicit_decision=explicit_decision,
        )

    fallback_decision = evaluate_sufficiency(
        _evidence(
            mode=mode,
            task_category=task_category,
            hits=fallback_retrieval.hits,
            freshness=collection_freshness(collections.get(fallback.collection)),
            thresholds_version=manifest.policy.sufficiency_thresholds_version,
        )
    )
    aggregate_hits = project_retrieval.hits + fallback_retrieval.hits
    aggregate_duration = project_retrieval.duration_ms + fallback_retrieval.duration_ms
    if fallback_decision.status is SufficiencyStatus.SUFFICIENT:
        return _materialize_context(
            manifest=manifest,
            projection=projection,
            mode=mode,
            task_category=task_category,
            route=route,
            retrieval=fallback_retrieval,
            hits=aggregate_hits,
            duration_ms=aggregate_duration,
            decision=fallback_decision,
            risk_reason=risk_reason,
            fallback_used=True,
            fallback_explicit_decision=explicit_decision,
            fallback_reason_codes=project_decision.reason_codes,
        )
    return context_outcome(
        project_id=manifest.project.id,
        mode=mode,
        task_category=task_category,
        route=route,
        retrieval=fallback_retrieval,
        hits=aggregate_hits,
        duration_ms=aggregate_duration,
        decision=fallback_decision,
        fallback_used=True,
        fallback_explicit_decision=explicit_decision,
        fallback_reason_codes=project_decision.reason_codes,
    )
