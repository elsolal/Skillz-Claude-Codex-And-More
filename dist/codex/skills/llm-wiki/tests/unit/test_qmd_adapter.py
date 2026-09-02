from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

from memory_cli.qmd_adapter import (
    MAX_OUTPUT_BYTES,
    QmdOutputError,
    QmdSearchStatus,
    QmdTimeoutError,
    parse_qmd_search,
    parse_qmd_status,
    parse_qmd_version,
    search_qmd,
)


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

    def test_normalizes_qmd_09_search_results(self) -> None:
        hits = parse_qmd_search(
            (FIXTURES / "search-results.json").read_text(),
            expected_collection="elsolal-wiki",
        )

        self.assertEqual(len(hits), 2)
        self.assertEqual(hits[0].docid, "#dfec5e")
        self.assertEqual(hits[0].collection, "elsolal-wiki")
        self.assertEqual(hits[0].relative_path.as_posix(), "entities/skillz-claude.md")
        self.assertEqual(hits[0].title, "Skillz-Claude")
        self.assertEqual(hits[0].score, 0.91)
        self.assertEqual(hits[0].snippet_line, 13)
        self.assertIn("agentic coding", hits[0].snippet)

    def test_search_uses_atomic_arguments_and_reports_empty(self) -> None:
        calls: list[tuple[list[str], dict[str, object]]] = []

        def runner(arguments: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            calls.append((arguments, kwargs))
            return subprocess.CompletedProcess(arguments, 0, "[]", "")

        outcome = search_qmd(
            "/tmp/qmd fixture",
            query="architecture; touch /tmp/never-created",
            collection="elsolal-wiki",
            limit=8,
            min_score=0.55,
            runner=runner,
            timeout_seconds=8.0,
        )

        self.assertEqual(outcome.status, QmdSearchStatus.EMPTY)
        self.assertEqual(outcome.hits, ())
        self.assertEqual(
            calls[0][0],
            [
                "/tmp/qmd fixture",
                "search",
                "architecture; touch /tmp/never-created",
                "--json",
                "-c",
                "elsolal-wiki",
                "-n",
                "8",
                "--min-score",
                "0.55",
            ],
        )
        self.assertIs(calls[0][1]["shell"], False)
        self.assertEqual(calls[0][1]["timeout"], 8.0)

    def test_distinguishes_timeout_invalid_json_and_oversized_output(self) -> None:
        def timeout_runner(
            arguments: list[str], **_: object
        ) -> subprocess.CompletedProcess[str]:
            raise subprocess.TimeoutExpired(arguments, 0.01)

        with self.assertRaises(QmdTimeoutError):
            search_qmd(
                "qmd",
                query="timeout",
                collection="elsolal-wiki",
                limit=3,
                min_score=0.7,
                runner=timeout_runner,
                timeout_seconds=0.01,
            )

        with self.assertRaises(QmdOutputError):
            parse_qmd_search(
                (FIXTURES / "search-invalid.json").read_text(),
                expected_collection="elsolal-wiki",
            )

        def oversized_runner(
            arguments: list[str], **_: object
        ) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(
                arguments,
                0,
                "[]",
                "x" * (MAX_OUTPUT_BYTES + 1),
            )

        with self.assertRaises(QmdOutputError):
            search_qmd(
                "qmd",
                query="large output",
                collection="elsolal-wiki",
                limit=3,
                min_score=0.7,
                runner=oversized_runner,
            )

    def test_rejects_wrong_collection_escaping_paths_and_invalid_timeout(self) -> None:
        payload = (FIXTURES / "search-results.json").read_text()
        with self.assertRaises(QmdOutputError):
            parse_qmd_search(payload, expected_collection="other-wiki")
        with self.assertRaises(QmdOutputError):
            parse_qmd_search(
                payload.replace(
                    "qmd://elsolal-wiki/entities/skillz-claude.md",
                    "qmd://elsolal-wiki/../secret.md",
                ),
                expected_collection="elsolal-wiki",
            )
        with self.assertRaises(ValueError):
            search_qmd(
                "qmd",
                query="timeout",
                collection="elsolal-wiki",
                limit=3,
                min_score=0.7,
                timeout_seconds=30.01,
            )
        with self.assertRaises(ValueError):
            search_qmd(
                "qmd",
                query="hostile manifest",
                collection="elsolal-wiki; touch /tmp/never-created",
                limit=3,
                min_score=0.7,
            )


if __name__ == "__main__":
    unittest.main()
