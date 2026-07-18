from __future__ import annotations

import sys
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT))

from memory_cli.contracts import (  # noqa: E402
    FreshnessStatus,
    ProvenanceKind,
    RetrievalMode,
    SufficiencyEvidence,
    SufficiencyHit,
    SufficiencyReason,
    SufficiencyStatus,
    TaskCategory,
)
from memory_cli.sufficiency import (  # noqa: E402
    DEFAULT_SUFFICIENCY_THRESHOLDS_VERSION,
    evaluate_sufficiency,
)


def hit(score: float, provenance: ProvenanceKind = ProvenanceKind.PAGE) -> SufficiencyHit:
    return SufficiencyHit(
        docid=f"#{round(score * 1_000_000):06x}",
        score=score,
        provenance=provenance,
    )


def evidence(
    mode: RetrievalMode,
    *hits: SufficiencyHit,
    category: TaskCategory = TaskCategory.GENERAL,
    freshness: FreshnessStatus = FreshnessStatus.FRESH,
    version: str = DEFAULT_SUFFICIENCY_THRESHOLDS_VERSION,
) -> SufficiencyEvidence:
    return SufficiencyEvidence(
        mode=mode,
        task_category=category,
        hits=tuple(hits),
        freshness=freshness,
        thresholds_version=version,
    )


class SufficiencyGateTests(unittest.TestCase):
    def test_project_stops_on_one_strong_fresh_hit_or_two_coverage_hits(self) -> None:
        strong = evaluate_sufficiency(evidence(RetrievalMode.PROJECT, hit(0.75)))
        covered = evaluate_sufficiency(
            evidence(RetrievalMode.PROJECT, hit(0.55), hit(0.55))
        )

        self.assertEqual(strong.status, SufficiencyStatus.SUFFICIENT)
        self.assertEqual(strong.reason_codes, ())
        self.assertEqual(covered.status, SufficiencyStatus.SUFFICIENT)

    def test_mode_boundaries_and_reason_order_are_deterministic(self) -> None:
        minimal = evaluate_sufficiency(evidence(RetrievalMode.MINIMAL, hit(0.749)))
        historical = evaluate_sufficiency(
            evidence(
                RetrievalMode.HISTORICAL,
                hit(0.44),
                category=TaskCategory.HISTORICAL,
            )
        )

        self.assertEqual(minimal.status, SufficiencyStatus.INSUFFICIENT)
        self.assertEqual(minimal.reason_codes, (SufficiencyReason.BELOW_SCORE,))
        self.assertEqual(
            historical.reason_codes,
            (
                SufficiencyReason.BELOW_SCORE,
                SufficiencyReason.INSUFFICIENT_COVERAGE,
                SufficiencyReason.MISSING_PROVENANCE,
                SufficiencyReason.TASK_REQUIRES_TRANSVERSE,
            ),
        )

    def test_historical_requires_two_hits_and_source_or_synthesis_provenance(self) -> None:
        weak_provenance = evaluate_sufficiency(
            evidence(RetrievalMode.HISTORICAL, hit(0.60), hit(0.55))
        )
        sourced = evaluate_sufficiency(
            evidence(
                RetrievalMode.HISTORICAL,
                hit(0.60, ProvenanceKind.SOURCE),
                hit(0.55),
            )
        )

        self.assertEqual(weak_provenance.status, SufficiencyStatus.INSUFFICIENT)
        self.assertIn(SufficiencyReason.MISSING_PROVENANCE, weak_provenance.reason_codes)
        self.assertEqual(sourced.status, SufficiencyStatus.SUFFICIENT)

    def test_stale_high_risk_is_blocked_but_low_risk_is_visible(self) -> None:
        high_risk = evaluate_sufficiency(
            evidence(
                RetrievalMode.PROJECT,
                hit(0.90),
                category=TaskCategory.SECURITY,
                freshness=FreshnessStatus.STALE,
            )
        )
        low_risk = evaluate_sufficiency(
            evidence(
                RetrievalMode.PROJECT,
                hit(0.90),
                freshness=FreshnessStatus.STALE,
            )
        )

        self.assertEqual(high_risk.status, SufficiencyStatus.BLOCKED)
        self.assertEqual(high_risk.reason_codes, (SufficiencyReason.STALE,))
        self.assertEqual(low_risk.status, SufficiencyStatus.SUFFICIENT)
        self.assertEqual(low_risk.reason_codes, (SufficiencyReason.STALE,))

    def test_unknown_required_evidence_is_ambiguous_without_hidden_judgment(self) -> None:
        decision = evaluate_sufficiency(
            evidence(
                RetrievalMode.PROJECT,
                hit(0.90),
                freshness=FreshnessStatus.UNKNOWN,
            )
        )

        self.assertEqual(decision.status, SufficiencyStatus.AMBIGUOUS)
        self.assertEqual(decision.reason_codes, (SufficiencyReason.AMBIGUOUS,))
        self.assertEqual(decision.evidence, evidence(
            RetrievalMode.PROJECT,
            hit(0.90),
            freshness=FreshnessStatus.UNKNOWN,
        ))

    def test_threshold_profile_version_is_reproducible_and_unknown_versions_fail(self) -> None:
        first = evaluate_sufficiency(evidence(RetrievalMode.PROJECT, hit(0.60)))
        second = evaluate_sufficiency(evidence(RetrievalMode.PROJECT, hit(0.60)))

        self.assertEqual(first, second)
        self.assertEqual(first.thresholds_version, "qmd-0.9-v1")
        with self.assertRaisesRegex(ValueError, "Unsupported sufficiency thresholds version"):
            evaluate_sufficiency(
                evidence(RetrievalMode.PROJECT, hit(0.90), version="future-v9")
            )


if __name__ == "__main__":
    unittest.main()
