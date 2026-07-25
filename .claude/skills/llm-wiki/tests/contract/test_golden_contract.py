from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT))

from memory_cli.golden import GoldenContractError, persist_golden_run  # noqa: E402
from memory_cli.receipts import GoldenTestOutcome  # noqa: E402
from memory_cli.render_human import render_golden_test_human  # noqa: E402
from memory_cli.render_json import golden_test_envelope  # noqa: E402


EXPECTED = SKILL_ROOT / "expected_outputs" / "memory" / "test-ready.json"


class GoldenOutputContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.outcome = GoldenTestOutcome(
            status="ready",
            exit_code=0,
            project_id="skillz-claude",
            run_id="run_20260725T120000000000Z_0123456789abcdef",
            occurred_at="2026-07-25T12:00:00.000000Z",
            estimator_version="utf8_bytes_div_4_v1",
            cases=(
                {
                    "case_id": "project-memory-route",
                    "expected_count": 1,
                    "baseline_hit_count": 1,
                    "bounded_hit_count": 1,
                    "fallback_used": False,
                    "context_reduction": 0.75,
                    "matches": [
                        {
                            "kind": "page",
                            "ordinal": 1,
                            "baseline_rank": 2,
                            "baseline_docid": "#111111",
                            "bounded_rank": 1,
                            "bounded_docid": "#dfec5e",
                        }
                    ],
                    "baseline": {
                        "status": "ready",
                        "docids": ["#000000", "#111111", "#222222"],
                        "estimated_context_tokens": 1000,
                    },
                    "bounded": {
                        "status": "sufficient",
                        "docids": ["#dfec5e"],
                        "estimated_context_tokens": 250,
                    },
                },
            ),
            aggregate={
                "retrieval_hit_rate": 1.0,
                "fallback_rate": 0.0,
                "median_context_reduction": 0.75,
            },
        )

    def test_json_envelope_matches_the_versioned_metadata_only_snapshot(self) -> None:
        envelope = golden_test_envelope(self.outcome)

        self.assertEqual(envelope, json.loads(EXPECTED.read_text(encoding="utf-8")))
        serialized = json.dumps(envelope)
        for forbidden in ("query", "prompt", "snippet", "content", "/Users/"):
            self.assertNotIn(forbidden, serialized)

    def test_human_renderer_preserves_every_aggregate_dimension(self) -> None:
        stream = io.StringIO()

        render_golden_test_human(self.outcome, stream=stream)

        output = stream.getvalue()
        self.assertIn("Cases: 1", output)
        self.assertIn("Retrieval hit rate: 100.0%", output)
        self.assertIn("Fallback rate: 0.0%", output)
        self.assertIn("Median context reduction: 75.0%", output)
        self.assertIn("utf8_bytes_div_4_v1", output)

    def test_run_publish_is_immutable_and_keeps_post_publish_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            state = root / "state"
            project.mkdir()
            diagnostic = {
                "code": "event_directory_fsync_failed",
                "message": "directory durability unavailable",
                "correction": "retry storage verification",
            }
            with patch(
                "memory_cli.golden.fsync_state_directory",
                return_value=(diagnostic,),
            ):
                path, diagnostics = persist_golden_run(
                    self.outcome,
                    state_dir=state,
                    project_root=project,
                )

            original = path.read_bytes()
            self.assertTrue(path.is_file())
            self.assertEqual(
                diagnostics[0]["code"],
                "golden_run_directory_fsync_failed",
            )
            with self.assertRaises(GoldenContractError) as raised:
                persist_golden_run(
                    self.outcome,
                    state_dir=state,
                    project_root=project,
                )
            self.assertEqual(raised.exception.code, "golden_run_exists")
            self.assertEqual(path.read_bytes(), original)

    def test_temp_cleanup_failure_keeps_the_published_run_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            state = root / "state"
            project.mkdir()

            with patch("pathlib.Path.unlink", side_effect=PermissionError("denied")):
                path, diagnostics = persist_golden_run(
                    self.outcome,
                    state_dir=state,
                    project_root=project,
                )

            self.assertTrue(path.is_file())
            self.assertEqual(
                diagnostics[0]["code"],
                "golden_run_temp_cleanup_failed",
            )


if __name__ == "__main__":
    unittest.main()
