from __future__ import annotations

import copy
import json
import math
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT))

from memory_cli.quality import (  # noqa: E402
    QualityContractError,
    calculate_quality_degradation,
    load_quality_record,
    load_quality_import,
    load_quality_rubric,
    persist_quality_import,
)


RUBRIC_FIXTURE = SKILL_ROOT / "tests" / "fixtures" / "quality-v1" / "rubric.json"
RECORD_FIXTURE = SKILL_ROOT / "tests" / "fixtures" / "quality-v1" / "record.json"


class QualityContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.rubric_payload = json.loads(RUBRIC_FIXTURE.read_text(encoding="utf-8"))
        self.record_payload = json.loads(RECORD_FIXTURE.read_text(encoding="utf-8"))

    def _write(self, name: str, payload: object) -> Path:
        path = self.root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_validates_versioned_weighted_rubric_and_clean_record(self) -> None:
        rubric = load_quality_rubric(self._write("rubric.json", self.rubric_payload))
        record = load_quality_import(
            self._write("quality.json", self.record_payload),
            rubric=rubric,
        )

        self.assertEqual(rubric.rubric_version, "quality-v1")
        self.assertTrue(math.isclose(sum(item.weight for item in rubric.dimensions), 1.0))
        self.assertEqual(record.reviewer_type, "human")
        self.assertAlmostEqual(record.quality_degradation, 0.03125)

    def test_rejects_unknown_raw_response_fields_and_invalid_reviewer(self) -> None:
        rubric = load_quality_rubric(self._write("rubric.json", self.rubric_payload))
        invalid_payloads = []

        raw_response = copy.deepcopy(self.record_payload)
        raw_response["response"] = "raw model answer"
        invalid_payloads.append((raw_response, "quality_import_schema_invalid"))

        reviewer = copy.deepcopy(self.record_payload)
        reviewer["reviewer_type"] = "anonymous"
        invalid_payloads.append((reviewer, "quality_reviewer_invalid"))

        for index, (payload, expected_code) in enumerate(invalid_payloads):
            with self.subTest(expected_code=expected_code):
                with self.assertRaises(QualityContractError) as raised:
                    load_quality_import(
                        self._write(f"invalid-{index}.json", payload),
                        rubric=rubric,
                    )
                self.assertEqual(raised.exception.code, expected_code)

    def test_degradation_is_zero_when_candidate_improves_and_rejects_zero_baseline(self) -> None:
        self.assertEqual(calculate_quality_degradation(90, 95), 0.0)

        with self.assertRaises(QualityContractError) as raised:
            calculate_quality_degradation(0, 0)

        self.assertEqual(raised.exception.code, "quality_baseline_invalid")

    def test_persists_one_private_immutable_record_linked_to_an_existing_run(self) -> None:
        project_root = self.root / "repo"
        state_dir = self.root / "state"
        project_root.mkdir()
        rubric = load_quality_rubric(self._write("rubric.json", self.rubric_payload))
        imported = load_quality_import(
            self._write("quality.json", self.record_payload),
            rubric=rubric,
        )
        run_dir = state_dir / "runs" / "skillz-claude"
        run_dir.mkdir(parents=True)
        run_path = run_dir / f"{imported.run_id}.json"
        run_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "run_id": imported.run_id,
                    "occurred_at": "2026-07-26T12:00:00.000000Z",
                    "project_id": "skillz-claude",
                    "estimator_version": "utf8_bytes_div_4_v1",
                    "cases": [],
                    "aggregate": {
                        "retrieval_hit_rate": 1.0,
                        "fallback_rate": 0.0,
                        "median_context_reduction": 0.5,
                    },
                }
            ),
            encoding="utf-8",
        )

        path, diagnostics = persist_quality_import(
            imported,
            project_id="skillz-claude",
            state_dir=state_dir,
            project_root=project_root,
        )
        record = load_quality_record(
            run_id=imported.run_id,
            project_id="skillz-claude",
            state_dir=state_dir,
            project_root=project_root,
        )

        self.assertEqual(diagnostics, ())
        self.assertEqual(record["reviewer_type"], "human")
        self.assertEqual(record["quality_degradation"], 0.03125)
        self.assertNotIn("response", path.read_text(encoding="utf-8"))
        if os.name == "posix":
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), 0o700)

        with self.assertRaises(QualityContractError) as raised:
            persist_quality_import(
                imported,
                project_id="skillz-claude",
                state_dir=state_dir,
                project_root=project_root,
            )
        self.assertEqual(raised.exception.code, "quality_record_exists")

        tampered = json.loads(path.read_text(encoding="utf-8"))
        tampered["quality_degradation"] = 0.0
        path.write_text(json.dumps(tampered), encoding="utf-8")
        with self.assertRaises(QualityContractError) as raised:
            load_quality_record(
                run_id=imported.run_id,
                project_id="skillz-claude",
                state_dir=state_dir,
                project_root=project_root,
            )
        self.assertEqual(raised.exception.code, "quality_record_invalid")


if __name__ == "__main__":
    unittest.main()
