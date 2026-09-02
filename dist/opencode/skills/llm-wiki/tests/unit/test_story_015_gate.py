from __future__ import annotations

import sys
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT))

from memory_cli.quality import evaluate_measurement_gate  # noqa: E402


class MeasurementGateTests(unittest.TestCase):
    def test_passes_only_when_holdout_retrieval_context_and_quality_pass(self) -> None:
        result = evaluate_measurement_gate(
            aggregate={
                "retrieval_hit_rate": 0.95,
                "fallback_rate": 0.0,
                "median_context_reduction": 0.55,
            },
            holdout_case_count=2,
            quality_degradation=0.05,
        )

        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["dimensions"]["quality"]["status"], "pass")

    def test_is_incomplete_without_quality_and_never_passes_without_holdout(self) -> None:
        aggregate = {
            "retrieval_hit_rate": 1.0,
            "fallback_rate": 0.0,
            "median_context_reduction": 0.75,
        }

        missing_quality = evaluate_measurement_gate(
            aggregate=aggregate,
            holdout_case_count=2,
            quality_degradation=None,
        )
        missing_holdout = evaluate_measurement_gate(
            aggregate=aggregate,
            holdout_case_count=0,
            quality_degradation=0.0,
        )

        self.assertEqual(missing_quality["status"], "incomplete")
        self.assertEqual(missing_holdout["status"], "incomplete")

    def test_quality_failure_overrides_context_success(self) -> None:
        result = evaluate_measurement_gate(
            aggregate={
                "retrieval_hit_rate": 1.0,
                "fallback_rate": 0.0,
                "median_context_reduction": 0.75,
            },
            holdout_case_count=2,
            quality_degradation=0.0500001,
        )

        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["dimensions"]["context"]["status"], "pass")
        self.assertEqual(result["dimensions"]["quality"]["status"], "fail")


if __name__ == "__main__":
    unittest.main()
