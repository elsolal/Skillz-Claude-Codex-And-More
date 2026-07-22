"""Pure, versioned and explainable sufficiency decisions."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import PurePosixPath

from .contracts import (
    DEFAULT_SUFFICIENCY_THRESHOLDS_VERSION,
    FreshnessStatus,
    ProvenanceKind,
    RetrievalMode,
    SufficiencyDecision,
    SufficiencyEvidence,
    SufficiencyReason,
    SufficiencyStatus,
    TaskCategory,
)


@dataclass(frozen=True, slots=True)
class ModeThresholds:
    candidate_score: float
    strong_score: float | None
    coverage_hits: int | None
    requires_historical_provenance: bool = False


SUFFICIENCY_PROFILES: dict[str, dict[RetrievalMode, ModeThresholds]] = {
    DEFAULT_SUFFICIENCY_THRESHOLDS_VERSION: {
        RetrievalMode.MINIMAL: ModeThresholds(
            candidate_score=0.70,
            strong_score=0.75,
            coverage_hits=None,
        ),
        RetrievalMode.PROJECT: ModeThresholds(
            candidate_score=0.55,
            strong_score=0.75,
            coverage_hits=2,
        ),
        RetrievalMode.HISTORICAL: ModeThresholds(
            candidate_score=0.45,
            strong_score=None,
            coverage_hits=2,
            requires_historical_provenance=True,
        ),
    }
}

REASON_ORDER = tuple(SufficiencyReason)
BLOCKING_FRESHNESS_CATEGORIES = {
    TaskCategory.SECURITY,
    TaskCategory.DATA,
    TaskCategory.HISTORICAL,
}
HISTORICAL_PROVENANCE = {ProvenanceKind.SOURCE, ProvenanceKind.SYNTHESIS}


def provenance_for_path(relative_path: PurePosixPath) -> ProvenanceKind:
    """Classify QMD-relative wiki paths once for retrieval and assembly."""

    first_part = relative_path.parts[0] if relative_path.parts else ""
    if first_part == "sources":
        return ProvenanceKind.SOURCE
    if first_part == "synthesis":
        return ProvenanceKind.SYNTHESIS
    if first_part:
        return ProvenanceKind.PAGE
    return ProvenanceKind.UNKNOWN


def _ordered(reasons: set[SufficiencyReason]) -> tuple[SufficiencyReason, ...]:
    return tuple(reason for reason in REASON_ORDER if reason in reasons)


def _decision(
    status: SufficiencyStatus,
    evidence: SufficiencyEvidence,
    reasons: set[SufficiencyReason],
) -> SufficiencyDecision:
    return SufficiencyDecision(
        status=status,
        reason_codes=_ordered(reasons),
        thresholds_version=evidence.thresholds_version,
        evidence=evidence,
    )


def thresholds_for(version: str, mode: RetrievalMode) -> ModeThresholds:
    profile = SUFFICIENCY_PROFILES.get(version)
    if profile is None:
        raise ValueError(f"Unsupported sufficiency thresholds version: {version}")
    return profile[mode]


def evaluate_sufficiency(evidence: SufficiencyEvidence) -> SufficiencyDecision:
    """Evaluate normalized evidence without I/O, hidden models or mutable state."""

    thresholds = thresholds_for(evidence.thresholds_version, evidence.mode)
    for candidate in evidence.hits:
        if not math.isfinite(candidate.score) or not 0 <= candidate.score <= 1:
            raise ValueError("Sufficiency hit scores must be finite values between zero and one.")

    qualified = tuple(
        candidate
        for candidate in evidence.hits
        if candidate.score >= thresholds.candidate_score
    )
    reasons: set[SufficiencyReason] = set()

    if evidence.freshness is FreshnessStatus.STALE:
        if (
            evidence.mode is RetrievalMode.HISTORICAL
            or evidence.task_category in BLOCKING_FRESHNESS_CATEGORIES
        ):
            return _decision(
                SufficiencyStatus.BLOCKED,
                evidence,
                {SufficiencyReason.STALE},
            )
        reasons.add(SufficiencyReason.STALE)

    sufficient = False
    if not evidence.hits:
        reasons.add(SufficiencyReason.NO_RESULT)
    elif evidence.mode is RetrievalMode.MINIMAL:
        sufficient = any(
            candidate.score >= (thresholds.strong_score or 1.0)
            for candidate in qualified
        )
        if not sufficient:
            reasons.add(SufficiencyReason.BELOW_SCORE)
    elif evidence.mode is RetrievalMode.PROJECT:
        strong = any(
            candidate.score >= (thresholds.strong_score or 1.0)
            for candidate in qualified
        )
        covered = len(qualified) >= (thresholds.coverage_hits or 0)
        sufficient = strong or covered
        if not qualified:
            reasons.add(SufficiencyReason.BELOW_SCORE)
        if not sufficient:
            reasons.add(SufficiencyReason.INSUFFICIENT_COVERAGE)
    else:
        covered = len(qualified) >= (thresholds.coverage_hits or 0)
        has_provenance = any(
            candidate.provenance in HISTORICAL_PROVENANCE
            for candidate in qualified
        )
        sufficient = covered and has_provenance
        if not qualified:
            reasons.add(SufficiencyReason.BELOW_SCORE)
        if not covered:
            reasons.add(SufficiencyReason.INSUFFICIENT_COVERAGE)
        if not has_provenance:
            reasons.add(SufficiencyReason.MISSING_PROVENANCE)

    if not sufficient and evidence.task_category is TaskCategory.HISTORICAL:
        reasons.add(SufficiencyReason.TASK_REQUIRES_TRANSVERSE)

    if sufficient and evidence.freshness is FreshnessStatus.UNKNOWN:
        return _decision(
            SufficiencyStatus.AMBIGUOUS,
            evidence,
            {SufficiencyReason.AMBIGUOUS},
        )
    return _decision(
        SufficiencyStatus.SUFFICIENT if sufficient else SufficiencyStatus.INSUFFICIENT,
        evidence,
        reasons,
    )


__all__ = [
    "DEFAULT_SUFFICIENCY_THRESHOLDS_VERSION",
    "SUFFICIENCY_PROFILES",
    "evaluate_sufficiency",
    "thresholds_for",
]
