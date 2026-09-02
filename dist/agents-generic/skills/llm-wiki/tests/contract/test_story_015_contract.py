from __future__ import annotations

import io
import json
import sys
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT))

from memory_cli.quality import evaluate_measurement_gate  # noqa: E402
from memory_cli.receipts import MeasurementGateOutcome, QualityRecordOutcome  # noqa: E402
from memory_cli.render_human import (  # noqa: E402
    render_measurement_gate_human,
    render_quality_record_human,
)
from memory_cli.render_json import (  # noqa: E402
    measurement_gate_envelope,
    quality_record_envelope,
)


EXPECTED = SKILL_ROOT / "expected_outputs" / "memory"
RUN_ID = "run_20260726T120000000000Z_0123456789abcdef"


class Story015OutputContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.quality = QualityRecordOutcome(
            status="ready",
            exit_code=0,
            project_id="skillz-claude",
            run_id=RUN_ID,
            rubric_version="quality-v1",
            baseline_score=96.0,
            score=93.0,
            reviewer_type="human",
            quality_degradation=0.03125,
        )
        gate = evaluate_measurement_gate(
            aggregate={
                "retrieval_hit_rate": 0.95,
                "fallback_rate": 0.0,
                "median_context_reduction": 0.55,
            },
            holdout_case_count=2,
            quality_degradation=0.05,
        )
        self.gate = MeasurementGateOutcome(
            status="pass",
            exit_code=0,
            project_id="skillz-claude",
            run_id=RUN_ID,
            gate=gate,
        )

    def test_quality_and_gate_json_match_versioned_snapshots(self) -> None:
        self.assertEqual(
            quality_record_envelope(self.quality),
            json.loads((EXPECTED / "test-quality-recorded.json").read_text()),
        )
        self.assertEqual(
            measurement_gate_envelope(self.gate),
            json.loads((EXPECTED / "test-gate-pass.json").read_text()),
        )
        serialized = json.dumps(
            [quality_record_envelope(self.quality), measurement_gate_envelope(self.gate)]
        )
        for forbidden in ('"response":', '"prompt":', '"query":', '"snippet":', "/Users/"):
            self.assertNotIn(forbidden, serialized)

    def test_human_renderers_preserve_provenance_thresholds_and_scope(self) -> None:
        quality_stream = io.StringIO()
        gate_stream = io.StringIO()

        render_quality_record_human(self.quality, stream=quality_stream)
        render_measurement_gate_human(self.gate, stream=gate_stream)

        self.assertIn("Rubric: quality-v1", quality_stream.getvalue())
        self.assertIn("Reviewer: human", quality_stream.getvalue())
        self.assertIn("Raw response stored: no", quality_stream.getvalue())
        self.assertIn("Quality: pass", gate_stream.getvalue())
        self.assertIn("Global rollout authorized: no", gate_stream.getvalue())


if __name__ == "__main__":
    unittest.main()
