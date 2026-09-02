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
    load_golden_suite,
    load_holdout_suite,
)


GOLDEN_FIXTURE = SKILL_ROOT / "tests" / "fixtures" / "golden-v1" / "valid.json"
HOLDOUT_FIXTURE = SKILL_ROOT / "tests" / "fixtures" / "holdout-v1" / "valid.json"


class HoldoutContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.visible = load_golden_suite(GOLDEN_FIXTURE)
        self.payload = json.loads(HOLDOUT_FIXTURE.read_text(encoding="utf-8"))
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.path = Path(self.temp_dir.name) / "holdout.local.json"

    def _load(self, payload: object | None = None):
        self.path.write_text(
            json.dumps(self.payload if payload is None else payload),
            encoding="utf-8",
        )
        return load_holdout_suite(self.path, visible_suite=self.visible)

    def test_loads_exactly_two_local_cases_for_twenty_percent_holdout(self) -> None:
        suite = self._load()

        self.assertEqual(suite.schema_version, 1)
        self.assertEqual(len(suite.cases), 2)
        self.assertEqual(len(suite.cases) / (len(self.visible.cases) + len(suite.cases)), 0.2)

    def test_rejects_less_than_twenty_percent_before_execution(self) -> None:
        self.payload["cases"] = self.payload["cases"][:1]

        with self.assertRaises(GoldenContractError) as raised:
            self._load()

        self.assertEqual(raised.exception.code, "holdout_case_count_invalid")

    def test_rejects_visible_ids_queries_and_functional_duplicates(self) -> None:
        visible_payload = json.loads(GOLDEN_FIXTURE.read_text(encoding="utf-8"))
        duplicate_variants = []

        duplicate_id = copy.deepcopy(self.payload)
        duplicate_id["cases"][0]["id"] = visible_payload["cases"][0]["id"]
        duplicate_variants.append(duplicate_id)

        duplicate_query = copy.deepcopy(self.payload)
        duplicate_query["cases"][0]["query"] = visible_payload["cases"][0]["query"]
        duplicate_variants.append(duplicate_query)

        duplicate_function = copy.deepcopy(self.payload)
        duplicate_function["cases"][0]["query"] = visible_payload["cases"][0]["query"]
        duplicate_function["cases"][0]["task_category"] = visible_payload["cases"][0][
            "task_category"
        ]
        duplicate_function["cases"][0]["expected"] = visible_payload["cases"][0][
            "expected"
        ]
        duplicate_function["cases"][0]["baseline"] = visible_payload["cases"][0][
            "baseline"
        ]
        duplicate_variants.append(duplicate_function)

        for payload in duplicate_variants:
            with self.subTest(payload=payload["cases"][0]):
                with self.assertRaises(GoldenContractError) as raised:
                    self._load(payload)
                self.assertEqual(raised.exception.code, "holdout_duplicates_visible")


if __name__ == "__main__":
    unittest.main()
