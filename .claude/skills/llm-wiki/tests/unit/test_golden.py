from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT))

from memory_cli.golden import (  # noqa: E402
    GoldenContractError,
    aggregate_case_results,
    load_golden_suite,
)


FIXTURE = SKILL_ROOT / "tests" / "fixtures" / "golden-v1" / "valid.json"


class GoldenContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.path = Path(self.temp_dir.name) / "golden.json"

    def _load(self, payload: object | None = None):
        self.path.write_text(
            json.dumps(self.payload if payload is None else payload),
            encoding="utf-8",
        )
        return load_golden_suite(self.path)

    def test_loads_exactly_eight_reproducible_cases(self) -> None:
        suite = self._load()

        self.assertEqual(suite.schema_version, 1)
        self.assertEqual(len(suite.cases), 8)
        self.assertEqual(suite.cases[0].case_id, "install-runtime")
        self.assertEqual(
            suite.cases[0].baseline_pages[1].as_posix(),
            "wiki/entities/skillz-claude.md",
        )

    def test_rejects_unknown_schema_incomplete_sets_and_duplicate_ids(self) -> None:
        invalid_payloads = []

        unknown = copy.deepcopy(self.payload)
        unknown["schema_version"] = 2
        invalid_payloads.append((unknown, "golden_schema_unknown"))

        incomplete = copy.deepcopy(self.payload)
        incomplete["cases"] = incomplete["cases"][:7]
        invalid_payloads.append((incomplete, "golden_case_count_invalid"))

        duplicate = copy.deepcopy(self.payload)
        duplicate["cases"][1]["id"] = duplicate["cases"][0]["id"]
        invalid_payloads.append((duplicate, "golden_case_id_duplicate"))

        for payload, expected_code in invalid_payloads:
            with self.subTest(expected_code=expected_code):
                with self.assertRaises(GoldenContractError) as raised:
                    self._load(payload)
                self.assertEqual(raised.exception.code, expected_code)

    def test_rejects_missing_expectations_baseline_and_unsafe_paths(self) -> None:
        invalid_payloads = []

        missing_expected = copy.deepcopy(self.payload)
        missing_expected["cases"][0]["expected"] = {"pages": [], "sources": []}
        invalid_payloads.append((missing_expected, "golden_expectations_empty"))

        missing_baseline = copy.deepcopy(self.payload)
        del missing_baseline["cases"][0]["baseline"]
        invalid_payloads.append((missing_baseline, "golden_case_schema_invalid"))

        traversal = copy.deepcopy(self.payload)
        traversal["cases"][0]["baseline"]["pages"][0] = "wiki/../secret.md"
        invalid_payloads.append((traversal, "golden_path_invalid"))

        absolute = copy.deepcopy(self.payload)
        absolute["cases"][0]["expected"]["pages"][0] = "/tmp/leak.md"
        invalid_payloads.append((absolute, "golden_path_invalid"))

        for payload, expected_code in invalid_payloads:
            with self.subTest(expected_code=expected_code):
                with self.assertRaises(GoldenContractError) as raised:
                    self._load(payload)
                self.assertEqual(raised.exception.code, expected_code)

    def test_aggregates_item_hits_fallbacks_and_even_median_reduction(self) -> None:
        cases = [
            {
                "expected_count": 2,
                "bounded_hit_count": 2,
                "fallback_used": False,
                "context_reduction": 0.25,
            },
            {
                "expected_count": 1,
                "bounded_hit_count": 0,
                "fallback_used": True,
                "context_reduction": 0.75,
            },
        ]

        aggregate = aggregate_case_results(cases)

        self.assertEqual(aggregate["retrieval_hit_rate"], 2 / 3)
        self.assertEqual(aggregate["fallback_rate"], 0.5)
        self.assertEqual(aggregate["median_context_reduction"], 0.5)


if __name__ == "__main__":
    unittest.main()
