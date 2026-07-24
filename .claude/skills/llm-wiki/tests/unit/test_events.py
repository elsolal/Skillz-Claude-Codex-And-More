from __future__ import annotations

import json
import os
import stat
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
    purge_project_events,
    read_event_file,
    resolve_state_dir,
)


NOW = datetime(2026, 7, 24, 12, 30, tzinfo=timezone.utc)


def context_metadata(*, project_id: str = "skillz-claude") -> dict[str, object]:
    return {
        "project_id": project_id,
        "mode": "project",
        "task_category": "architecture",
        "status": "sufficient",
        "route": ["elsolal-wiki"],
        "retrieved": [
            {
                "docid": "#a1b2c3",
                "collection": "elsolal-wiki",
                "path": "wiki/entities/skillz-claude.md",
                "score": 0.86,
            }
        ],
        "read": [
            {
                "docid": "#a1b2c3",
                "collection": "elsolal-wiki",
                "path": "wiki/entities/skillz-claude.md",
            }
        ],
        "estimated_context_tokens": 840,
        "estimator_version": "utf8_bytes_div_4_v1",
        "budget_tokens": 2500,
        "duration_ms": 1200,
        "freshness": "fresh",
        "fallback_reason_codes": [],
        "risk_reason": None,
    }


class EventContractUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.state_dir = self.root / "state"

    def test_context_event_v1_has_a_closed_metadata_only_shape(self) -> None:
        event = build_context_event(
            context_metadata(),
            occurred_at=NOW,
            event_id="mem_20260724T123000000000Z_0123456789abcdef",
        )

        self.assertEqual(
            list(event),
            [
                "schema_version",
                "event_id",
                "event_type",
                "occurred_at",
                "project_id",
                "payload",
            ],
        )
        self.assertEqual(event["schema_version"], 1)
        self.assertEqual(event["event_type"], "context_completed")
        self.assertEqual(event["occurred_at"], "2026-07-24T12:30:00Z")
        self.assertEqual(event["project_id"], "skillz-claude")
        self.assertEqual(
            list(event["payload"]),
            [
                "mode",
                "task_category",
                "status",
                "route",
                "retrieved",
                "read",
                "estimated_context_tokens",
                "estimator_version",
                "budget_tokens",
                "duration_ms",
                "freshness",
                "fallback_reason_codes",
                "risk_reason",
            ],
        )
        serialized = json.dumps(event)
        for forbidden in ("query", "prompt", "response", "snippet", "transcript"):
            self.assertNotIn(forbidden, serialized.lower())

    def test_state_dir_precedence_and_posix_default(self) -> None:
        home = self.root / "home"
        self.assertEqual(
            resolve_state_dir(
                environ={"SKILLZ_MEMORY_STATE_DIR": str(self.root / "explicit")},
                home=home,
            ),
            self.root / "explicit",
        )
        self.assertEqual(
            resolve_state_dir(
                environ={"XDG_STATE_HOME": str(self.root / "xdg")},
                home=home,
            ),
            self.root / "xdg" / "skillz-memory",
        )
        self.assertEqual(
            resolve_state_dir(environ={}, home=home),
            home / ".local" / "state" / "skillz-memory",
        )

    @unittest.skipIf(os.name != "posix", "POSIX permission bits are not portable")
    def test_append_creates_private_directories_and_files(self) -> None:
        event = build_context_event(context_metadata(), occurred_at=NOW)
        event_path = append_event(
            event,
            state_dir=self.state_dir,
            project_root=self.repo,
        )

        self.assertEqual(stat.S_IMODE(self.state_dir.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(event_path.parent.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(event_path.stat().st_mode), 0o600)

    def test_truncated_tail_keeps_valid_prefix_and_reports_corruption(self) -> None:
        event = build_context_event(context_metadata(), occurred_at=NOW)
        event_path = append_event(
            event,
            state_dir=self.state_dir,
            project_root=self.repo,
        )
        with event_path.open("ab") as stream:
            stream.write(b'{"schema_version":1,"event_id":"truncated"')

        result = read_event_file(event_path)

        self.assertEqual(result.events, (event,))
        self.assertEqual(len(result.diagnostics), 1)
        self.assertEqual(result.diagnostics[0]["code"], "truncated_event_tail")

    def test_complete_but_contract_invalid_final_line_is_not_treated_as_truncation(self) -> None:
        event = build_context_event(context_metadata(), occurred_at=NOW)
        event_path = append_event(
            event,
            state_dir=self.state_dir,
            project_root=self.repo,
        )
        invalid = dict(event)
        invalid["payload"] = {**event["payload"], "query": "private"}
        with event_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(invalid) + "\n")

        with self.assertRaises(EventIntegrityError) as raised:
            read_event_file(event_path)

        self.assertEqual(raised.exception.code, "event_log_corrupt")

    def test_retention_and_force_purge_are_project_isolated(self) -> None:
        old = datetime(2026, 5, 1, 12, tzinfo=timezone.utc)
        fresh = datetime(2026, 7, 20, 12, tzinfo=timezone.utc)
        for project_id, occurred_at in (
            ("skillz-claude", old),
            ("skillz-claude", fresh),
            ("other-project", old),
        ):
            append_event(
                build_context_event(
                    context_metadata(project_id=project_id),
                    occurred_at=occurred_at,
                ),
                state_dir=self.state_dir,
                project_root=self.repo,
            )

        nominal = purge_project_events(
            "skillz-claude",
            retention_days=30,
            state_dir=self.state_dir,
            project_root=self.repo,
            now=NOW,
        )
        self.assertEqual(nominal.deleted_events, 1)
        self.assertEqual(nominal.retained_events, 1)
        self.assertTrue((self.state_dir / "events" / "other-project").exists())

        forced = purge_project_events(
            "skillz-claude",
            retention_days=30,
            state_dir=self.state_dir,
            project_root=self.repo,
            now=NOW,
            force=True,
        )
        self.assertEqual(forced.deleted_events, 1)
        self.assertFalse((self.state_dir / "events" / "skillz-claude").exists())
        self.assertTrue((self.state_dir / "events" / "other-project").exists())

    def test_state_dir_inside_project_is_rejected(self) -> None:
        event = build_context_event(context_metadata(), occurred_at=NOW)
        with self.assertRaises(EventIntegrityError) as raised:
            append_event(
                event,
                state_dir=self.repo / ".state",
                project_root=self.repo,
            )

        self.assertEqual(raised.exception.exit_code, 50)
        self.assertEqual(raised.exception.code, "state_dir_in_project")

    @unittest.skipIf(os.name != "posix", "symlink behavior is platform-specific")
    def test_project_event_symlink_cannot_escape_the_state_root(self) -> None:
        outside = self.root / "outside"
        outside.mkdir()
        (self.state_dir / "events").mkdir(parents=True)
        (self.state_dir / "events" / "skillz-claude").symlink_to(
            outside,
            target_is_directory=True,
        )

        with self.assertRaises(EventIntegrityError) as raised:
            append_event(
                build_context_event(context_metadata(), occurred_at=NOW),
                state_dir=self.state_dir,
                project_root=self.repo,
            )

        self.assertEqual(raised.exception.code, "event_store_escape")
        self.assertEqual(list(outside.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
