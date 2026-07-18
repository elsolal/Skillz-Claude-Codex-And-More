from __future__ import annotations

import unittest
from pathlib import Path

from memory_cli.qmd_adapter import QmdOutputError, parse_qmd_status, parse_qmd_version


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "qmd-0.9"


class QmdAdapterTests(unittest.TestCase):
    def test_parses_supported_version_and_collection_freshness(self) -> None:
        self.assertEqual(parse_qmd_version((FIXTURES / "version.txt").read_text()), (0, 9, 0))

        status = parse_qmd_status((FIXTURES / "status.txt").read_text())

        self.assertEqual(status["elsolal-wiki"].files, 179)
        self.assertEqual(status["elsolal-wiki"].age_seconds, 3 * 60 * 60)
        self.assertEqual(status["pleepole-wiki"].age_seconds, 18 * 24 * 60 * 60)

    def test_rejects_unknown_version_and_malformed_status(self) -> None:
        with self.assertRaises(QmdOutputError):
            parse_qmd_version("qmd development")
        with self.assertRaises(QmdOutputError):
            parse_qmd_status((FIXTURES / "status-malformed.txt").read_text())

    def test_accepts_relative_ages_used_by_qmd_09(self) -> None:
        for label, expected in (
            ("just now", 0),
            ("45s ago", 45),
            ("12m ago", 720),
            ("2w ago", 1_209_600),
        ):
            with self.subTest(label=label):
                output = (
                    "Collections\n"
                    "  project-wiki (qmd://project-wiki/)\n"
                    f"    Files:    4 (updated {label})\n"
                )
                self.assertEqual(
                    parse_qmd_status(output)["project-wiki"].age_seconds,
                    expected,
                )


if __name__ == "__main__":
    unittest.main()
