from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT))

from memory_cli.projection import ProjectionError, parse_store_arguments  # noqa: E402


class StoreAssignmentTests(unittest.TestCase):
    def test_parses_the_single_absolute_project_store(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()

            stores = parse_store_arguments([f"project={root}"])

        self.assertEqual(stores, {"project": root})

    def test_rejects_missing_relative_unknown_and_duplicate_stores(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            cases = (
                ([], "missing_store"),
                (["project=relative/vault"], "local_root_not_absolute"),
                ([f"transverse={root}"], "unknown_store"),
                ([f"project={root}", f"project={root}"], "duplicate_store"),
                (["project"], "invalid_store_assignment"),
            )

            for assignments, expected_code in cases:
                with self.subTest(assignments=assignments), self.assertRaises(ProjectionError) as raised:
                    parse_store_arguments(assignments)

                self.assertEqual(raised.exception.code, expected_code)
                self.assertEqual(raised.exception.exit_code, 30)

    def test_rejects_an_unavailable_absolute_root_without_echoing_it(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "private" / "missing-vault"

            with self.assertRaises(ProjectionError) as raised:
                parse_store_arguments([f"project={missing}"])

        self.assertEqual(raised.exception.code, "local_root_unavailable")
        self.assertNotIn(str(missing), raised.exception.message)

    def test_rejects_malformed_or_unknown_store_without_echoing_local_input(self) -> None:
        sensitive_inputs = (
            "/Users/example/Secret Vault",
            "/Users/example/private=/absolute/vault",
        )
        for sensitive_input in sensitive_inputs:
            with self.subTest(sensitive_input=sensitive_input), self.assertRaises(
                ProjectionError
            ) as raised:
                parse_store_arguments([sensitive_input])

            self.assertNotIn("/Users/example", raised.exception.message)


if __name__ == "__main__":
    unittest.main()
