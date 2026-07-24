from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT))

from memory_cli.events import (  # noqa: E402
    EventIntegrityError,
    append_event,
    build_context_event,
    build_usage_attestation_event,
)
from unit.test_events import context_metadata  # noqa: E402


NOW = datetime(2026, 7, 24, 12, 30, tzinfo=timezone.utc)


class MetadataOnlyEventContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.state_dir = self.root / "state"
        self.event = build_context_event(context_metadata(), occurred_at=NOW)

    def assert_rejected_without_append(self, event: dict[str, object]) -> None:
        with self.assertRaises(EventIntegrityError) as raised:
            append_event(
                event,
                state_dir=self.state_dir,
                project_root=self.repo,
            )
        self.assertEqual(raised.exception.exit_code, 50)
        self.assertFalse(any(self.state_dir.rglob("*.jsonl")))

    def test_unknown_or_content_bearing_keys_are_rejected(self) -> None:
        for key in ("query", "prompt", "response", "transcript", "snippet", "body"):
            with self.subTest(key=key):
                event = copy.deepcopy(self.event)
                event["payload"][key] = "private user material"
                self.assert_rejected_without_append(event)

    def test_sensitive_keys_are_rejected_at_any_depth(self) -> None:
        for key in ("api_key", "password", "authorization", "private_key", "access_token"):
            with self.subTest(key=key):
                event = copy.deepcopy(self.event)
                event["payload"]["retrieved"][0][key] = "sensitive"
                self.assert_rejected_without_append(event)

    def test_absolute_posix_windows_and_unc_paths_are_rejected(self) -> None:
        for path in (
            "/Users/example/private.md",
            r"C:\\Users\\example\\private.md",
            r"\\\\server\\share\\private.md",
        ):
            with self.subTest(path=path):
                event = copy.deepcopy(self.event)
                event["payload"]["retrieved"][0]["path"] = path
                self.assert_rejected_without_append(event)

    def test_secret_shaped_values_are_rejected(self) -> None:
        for value in (
            "sk-proj-abcdefghijklmnopqrstuvwxyz123456",
            "ghp_abcdefghijklmnopqrstuvwxyz1234567890",
            "-----BEGIN PRIVATE KEY-----",
            "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.signature",
        ):
            with self.subTest(value=value):
                event = copy.deepcopy(self.event)
                event["payload"]["route"] = [value]
                self.assert_rejected_without_append(event)

    def test_usage_attestations_keep_the_same_privacy_boundary(self) -> None:
        attestation = build_usage_attestation_event(
            self.event,
            used=("#a1b2c3",),
            cited=(),
            citation_only=(),
            impact_codes=(),
            occurred_at=NOW,
        )
        for key in ("query", "prompt", "response", "transcript", "snippet", "body"):
            with self.subTest(key=key):
                event = copy.deepcopy(attestation)
                event["payload"][key] = "private user material"
                self.assert_rejected_without_append(event)


if __name__ == "__main__":
    unittest.main()
