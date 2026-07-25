from __future__ import annotations

import json
import os
import stat
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch


SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT))

from memory_cli.events import (  # noqa: E402
    EventIntegrityError,
    append_event,
    append_event_batch_atomically,
    build_context_event,
    build_usage_attestation_event,
    purge_project_events,
    read_event_file,
    resolve_state_dir,
    validate_event,
)
from memory_cli.conflicts import (  # noqa: E402
    build_memory_conflict_event,
    build_memory_debt_action_event,
)
from memory_cli.contracts import (  # noqa: E402
    ConflictCategory,
    ConflictEvidenceType,
    ConflictRisk,
    DebtAction,
)
from memory_cli.session_events import (  # noqa: E402
    append_memory_debt_action,
    append_usage_attestation,
)
from memory_cli.receipts import FinishOutcome  # noqa: E402


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

    def test_usage_attestation_v1_is_closed_versioned_and_linked(self) -> None:
        parent = build_context_event(
            context_metadata(),
            occurred_at=NOW,
            event_id="mem_20260724T123000000000Z_0123456789abcdef",
        )

        event = build_usage_attestation_event(
            parent,
            used=("#a1b2c3", "#a1b2c3"),
            cited=("#a1b2c3",),
            citation_only=(),
            impact_codes=("project_convention_applied",),
            occurred_at=NOW,
            event_id="att_20260724T123000000000Z_fedcba9876543210",
        )

        self.assertEqual(
            list(event),
            [
                "schema_version",
                "event_id",
                "event_type",
                "occurred_at",
                "project_id",
                "parent_event_id",
                "payload",
            ],
        )
        self.assertEqual(event["event_type"], "usage_attested")
        self.assertEqual(event["parent_event_id"], parent["event_id"])
        self.assertEqual(
            event["payload"],
            {
                "impact_taxonomy_version": "impact-v1",
                "used": ["#a1b2c3"],
                "cited": ["#a1b2c3"],
                "citation_only": [],
                "impact_codes": ["project_convention_applied"],
            },
        )

    def test_conflict_and_debt_action_events_are_closed_and_linked(self) -> None:
        parent = build_context_event(
            context_metadata(),
            occurred_at=NOW,
            event_id="mem_20260724T123000000000Z_0123456789abcdef",
        )
        conflict = build_memory_conflict_event(
            parent,
            memory_docid="#a1b2c3",
            repository_path="src/current-contract.py",
            evidence_type=ConflictEvidenceType.CONTRACT,
            category=ConflictCategory.ARCHITECTURE,
            risk=ConflictRisk.HIGH,
            prepare_debt=True,
            occurred_at=NOW,
            event_id="con_20260724T123000000000Z_0123456789abcdef",
        )

        self.assertEqual(conflict["event_type"], "memory_conflict")
        self.assertEqual(conflict["parent_event_id"], parent["event_id"])
        self.assertEqual(conflict["payload"]["precedence"], "repository")
        self.assertTrue(conflict["payload"]["requires_human"])
        self.assertEqual(
            conflict["payload"]["memory"],
            {"docid": "#a1b2c3", "path": "wiki/entities/skillz-claude.md"},
        )

        action = build_memory_debt_action_event(
            conflict,
            action=DebtAction.IGNORE,
            reason="not_actionable",
            snooze_until=None,
            occurred_at=NOW,
            event_id="deb_20260724T123000000000Z_0123456789abcdef",
        )
        self.assertEqual(action["event_type"], "memory_debt_action")
        self.assertEqual(action["parent_event_id"], conflict["event_id"])
        self.assertEqual(action["payload"]["action"], "ignore")
        self.assertEqual(action["payload"]["reason"], "not_actionable")

    def test_related_event_batch_is_all_or_nothing_and_retryable(self) -> None:
        parent = build_context_event(context_metadata(), occurred_at=NOW)
        event_path = append_event(
            parent,
            state_dir=self.state_dir,
            project_root=self.repo,
        )
        attestation = build_usage_attestation_event(
            parent,
            used=("#a1b2c3",),
            cited=(),
            citation_only=(),
            impact_codes=(),
            occurred_at=NOW,
        )
        conflict = build_memory_conflict_event(
            parent,
            memory_docid="#a1b2c3",
            repository_path="src/current-contract.py",
            evidence_type=ConflictEvidenceType.CONTRACT,
            category=ConflictCategory.ARCHITECTURE,
            risk=ConflictRisk.HIGH,
            prepare_debt=True,
            occurred_at=NOW,
        )

        with patch("memory_cli.events.os.replace", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                append_event_batch_atomically(
                    event_path,
                    (attestation, conflict),
                )

        self.assertEqual(read_event_file(event_path).events, (parent,))

        append_event_batch_atomically(event_path, (attestation, conflict))
        self.assertEqual(
            [event["event_type"] for event in read_event_file(event_path).events],
            ["context_completed", "usage_attested", "memory_conflict"],
        )

    def test_first_append_durably_prepares_every_directory_entry(self) -> None:
        nested_state = self.root / "missing" / "nested" / "state"
        parent = build_context_event(context_metadata(), occurred_at=NOW)
        fsynced_directories: list[Path] = []

        def track_directory_fsync(path: Path) -> tuple[dict[str, str], ...]:
            fsynced_directories.append(path)
            return ()

        with patch(
            "memory_cli.events._fsync_directory",
            side_effect=track_directory_fsync,
        ):
            event_path = append_event(
                parent,
                state_dir=nested_state,
                project_root=self.repo,
            )

        resolved_state = nested_state.resolve()
        expected_barriers = {
            self.root.resolve(),
            resolved_state.parent.parent,
            resolved_state.parent,
            resolved_state,
            resolved_state / "events",
            resolved_state / "events" / "skillz-claude",
        }
        self.assertTrue(expected_barriers.issubset(set(fsynced_directories)))
        self.assertEqual(read_event_file(event_path).events, (parent,))

    def test_bootstrap_fsync_failure_precedes_event_acknowledgement(self) -> None:
        parent = build_context_event(context_metadata(), occurred_at=NOW)
        diagnostic = (
            {
                "code": "event_directory_fsync_failed",
                "message": "Directory durability unavailable.",
                "correction": "Retry.",
            },
        )

        with patch(
            "memory_cli.events._fsync_directory",
            return_value=diagnostic,
        ):
            with self.assertRaises(EventIntegrityError) as raised:
                append_event(
                    parent,
                    state_dir=self.state_dir,
                    project_root=self.repo,
                )

        self.assertEqual(raised.exception.code, "event_store_unavailable")
        self.assertEqual(list(self.state_dir.rglob("*.jsonl")), [])

        event_path = append_event(
            parent,
            state_dir=self.state_dir,
            project_root=self.repo,
        )
        self.assertEqual(read_event_file(event_path).events, (parent,))

    def test_post_replace_fsync_failure_returns_ids_and_reconciles_retry(self) -> None:
        evidence = self.repo / "current-contract.py"
        evidence.write_text("CURRENT = True\n", encoding="utf-8")
        parent = build_context_event(context_metadata(), occurred_at=NOW)
        event_path = append_event(
            parent,
            state_dir=self.state_dir,
            project_root=self.repo,
        )
        real_fsync = os.fsync

        def fail_directory_fsync(descriptor: int) -> None:
            if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                raise OSError("directory durability unavailable")
            real_fsync(descriptor)

        arguments = {
            "project_id": "skillz-claude",
            "parent_event_id": parent["event_id"],
            "used": ("#a1b2c3",),
            "cited": (),
            "citation_only": (),
            "impact_codes": (),
            "conflict_docid": "#a1b2c3",
            "repository_path": "current-contract.py",
            "evidence_type": ConflictEvidenceType.CONTRACT,
            "conflict_category": ConflictCategory.ARCHITECTURE,
            "conflict_risk": ConflictRisk.HIGH,
            "prepare_debt": True,
            "state_dir": self.state_dir,
            "project_root": self.repo,
            "occurred_at": NOW,
        }
        with patch("memory_cli.events.os.fsync", side_effect=fail_directory_fsync):
            uncertain = append_usage_attestation(**arguments)

        self.assertEqual(
            uncertain.diagnostics[0]["code"],
            "event_directory_fsync_failed",
        )
        receipt = FinishOutcome(
            project_id="skillz-claude",
            parent_event=uncertain.parent_event,
            attestation_event=uncertain.event,
            conflict_event=uncertain.conflict_event,
            diagnostics=uncertain.diagnostics,
        )
        self.assertEqual(receipt.status, "degraded")
        self.assertEqual(receipt.exit_code, 50)
        self.assertEqual(
            [event["event_type"] for event in read_event_file(event_path).events],
            ["context_completed", "usage_attested", "memory_conflict"],
        )

        evidence.unlink()
        reconciled = append_usage_attestation(**arguments)
        self.assertEqual(reconciled.diagnostics, ())
        self.assertEqual(reconciled.event["event_id"], uncertain.event["event_id"])
        self.assertEqual(
            reconciled.conflict_event["event_id"],
            uncertain.conflict_event["event_id"],
        )
        self.assertEqual(len(read_event_file(event_path).events), 3)

        with self.assertRaises(EventIntegrityError) as raised:
            append_usage_attestation(
                **{**arguments, "conflict_risk": ConflictRisk.LOW}
            )
        self.assertEqual(raised.exception.code, "finish_replay_mismatch")

    def test_purge_reports_directory_fsync_failure_after_visible_rewrite(self) -> None:
        old_event = build_context_event(
            context_metadata(),
            occurred_at=datetime(2026, 6, 1, 10, tzinfo=timezone.utc),
        )
        fresh_event = build_context_event(
            context_metadata(),
            occurred_at=datetime(2026, 6, 25, 10, tzinfo=timezone.utc),
        )
        event_path = append_event(
            old_event,
            state_dir=self.state_dir,
            project_root=self.repo,
        )
        append_event(
            fresh_event,
            state_dir=self.state_dir,
            project_root=self.repo,
        )
        real_fsync = os.fsync

        def fail_directory_fsync(descriptor: int) -> None:
            if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                raise OSError("directory durability unavailable")
            real_fsync(descriptor)

        with patch("memory_cli.events.os.fsync", side_effect=fail_directory_fsync):
            outcome = purge_project_events(
                "skillz-claude",
                retention_days=30,
                state_dir=self.state_dir,
                project_root=self.repo,
                now=datetime(2026, 7, 24, tzinfo=timezone.utc),
            )

        self.assertEqual(outcome.status, "degraded")
        self.assertEqual(outcome.exit_code, 50)
        self.assertEqual(
            outcome.diagnostics[0]["code"],
            "event_directory_fsync_failed",
        )
        self.assertEqual(read_event_file(event_path).events, (fresh_event,))

        directory_fsyncs = 0

        def track_directory_fsync(descriptor: int) -> None:
            nonlocal directory_fsyncs
            if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                directory_fsyncs += 1
            real_fsync(descriptor)

        with patch("memory_cli.events.os.fsync", side_effect=track_directory_fsync):
            reconciled = purge_project_events(
                "skillz-claude",
                retention_days=30,
                state_dir=self.state_dir,
                project_root=self.repo,
                now=datetime(2026, 7, 24, tzinfo=timezone.utc),
            )

        self.assertEqual(reconciled.status, "ready")
        self.assertGreaterEqual(directory_fsyncs, 1)

    def test_force_purge_removes_abandoned_atomic_temporary_file(self) -> None:
        event = build_context_event(context_metadata(), occurred_at=NOW)
        event_path = append_event(
            event,
            state_dir=self.state_dir,
            project_root=self.repo,
        )
        abandoned = event_path.with_name(f".{event_path.name}.crashcopy")
        abandoned.write_bytes(event_path.read_bytes())

        outcome = purge_project_events(
            "skillz-claude",
            retention_days=30,
            force=True,
            state_dir=self.state_dir,
            project_root=self.repo,
            now=NOW,
        )

        self.assertEqual(outcome.status, "ready")
        self.assertEqual(outcome.deleted_events, 1)
        self.assertEqual(outcome.removed_files, 2)
        self.assertFalse(event_path.exists())
        self.assertFalse(abandoned.exists())

    def test_retention_deletes_descendants_of_expired_parent(self) -> None:
        evidence = self.repo / "current-contract.py"
        evidence.write_text("CURRENT = True\n", encoding="utf-8")
        parent = build_context_event(
            context_metadata(),
            occurred_at=datetime(2026, 6, 1, 10, tzinfo=timezone.utc),
        )
        append_event(
            parent,
            state_dir=self.state_dir,
            project_root=self.repo,
        )
        finish = append_usage_attestation(
            project_id="skillz-claude",
            parent_event_id=parent["event_id"],
            used=("#a1b2c3",),
            cited=(),
            citation_only=(),
            impact_codes=(),
            conflict_docid="#a1b2c3",
            repository_path="current-contract.py",
            evidence_type=ConflictEvidenceType.CONTRACT,
            conflict_category=ConflictCategory.ARCHITECTURE,
            conflict_risk=ConflictRisk.HIGH,
            prepare_debt=True,
            state_dir=self.state_dir,
            project_root=self.repo,
            occurred_at=datetime(2026, 6, 1, 11, tzinfo=timezone.utc),
        )
        assert finish.conflict_event is not None
        append_memory_debt_action(
            project_id="skillz-claude",
            parent_event_id=finish.conflict_event["event_id"],
            action=DebtAction.FIX,
            reason=None,
            snooze_until=None,
            state_dir=self.state_dir,
            project_root=self.repo,
            occurred_at=datetime(2026, 7, 20, 10, tzinfo=timezone.utc),
        )

        outcome = purge_project_events(
            "skillz-claude",
            retention_days=30,
            state_dir=self.state_dir,
            project_root=self.repo,
            now=datetime(2026, 7, 25, tzinfo=timezone.utc),
        )

        self.assertEqual(outcome.deleted_events, 4)
        self.assertEqual(outcome.retained_events, 0)
        self.assertFalse(any(self.state_dir.rglob("*.jsonl")))

    def test_expired_snooze_replay_reconciles_directory_fsync_failure(self) -> None:
        evidence = self.repo / "current-contract.py"
        evidence.write_text("CURRENT = True\n", encoding="utf-8")
        parent = build_context_event(
            context_metadata(),
            occurred_at=datetime(2026, 7, 20, 10, tzinfo=timezone.utc),
        )
        append_event(
            parent,
            state_dir=self.state_dir,
            project_root=self.repo,
        )
        finish = append_usage_attestation(
            project_id="skillz-claude",
            parent_event_id=parent["event_id"],
            used=("#a1b2c3",),
            cited=(),
            citation_only=(),
            impact_codes=(),
            conflict_docid="#a1b2c3",
            repository_path="current-contract.py",
            evidence_type=ConflictEvidenceType.CONTRACT,
            conflict_category=ConflictCategory.ARCHITECTURE,
            conflict_risk=ConflictRisk.HIGH,
            prepare_debt=True,
            state_dir=self.state_dir,
            project_root=self.repo,
            occurred_at=datetime(2026, 7, 20, 11, tzinfo=timezone.utc),
        )
        assert finish.conflict_event is not None
        real_fsync = os.fsync

        def fail_directory_fsync(descriptor: int) -> None:
            if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                raise OSError("directory durability unavailable")
            real_fsync(descriptor)

        arguments = {
            "project_id": "skillz-claude",
            "parent_event_id": finish.conflict_event["event_id"],
            "action": DebtAction.SNOOZE,
            "reason": None,
            "snooze_until": "2026-08-02",
            "state_dir": self.state_dir,
            "project_root": self.repo,
            "occurred_at": datetime(2026, 8, 1, 10, tzinfo=timezone.utc),
        }
        with (
            patch("memory_cli.conflicts.datetime") as conflicts_datetime,
            patch("memory_cli.events.os.fsync", side_effect=fail_directory_fsync),
        ):
            conflicts_datetime.now.return_value = datetime(
                2026, 8, 1, tzinfo=timezone.utc
            )
            uncertain = append_memory_debt_action(**arguments)

        self.assertEqual(
            uncertain.diagnostics[0]["code"],
            "event_directory_fsync_failed",
        )
        directory_fsyncs = 0

        def track_directory_fsync(descriptor: int) -> None:
            nonlocal directory_fsyncs
            if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                directory_fsyncs += 1
            real_fsync(descriptor)

        with (
            patch("memory_cli.conflicts.datetime") as conflicts_datetime,
            patch(
                "memory_cli.events.os.fsync",
                side_effect=track_directory_fsync,
            ),
        ):
            conflicts_datetime.now.return_value = datetime(
                2026, 8, 2, tzinfo=timezone.utc
            )
            with self.assertRaises(EventIntegrityError) as raised:
                append_memory_debt_action(**arguments)

        self.assertEqual(raised.exception.code, "debt_already_reviewed")
        self.assertGreaterEqual(directory_fsyncs, 1)
        august_path = (
            self.state_dir / "events" / "skillz-claude" / "2026-08.jsonl"
        )
        august_events = read_event_file(august_path).events
        self.assertEqual(august_events[0]["event_id"], uncertain.event["event_id"])

    def test_attested_docids_must_be_retrieved_and_citations_justified(self) -> None:
        parent = build_context_event(context_metadata(), occurred_at=NOW)

        with self.assertRaisesRegex(EventIntegrityError, "#missing"):
            build_usage_attestation_event(
                parent,
                used=("#missing",),
                cited=(),
                citation_only=(),
                impact_codes=(),
                occurred_at=NOW,
            )

        with self.assertRaisesRegex(EventIntegrityError, "#a1b2c3"):
            build_usage_attestation_event(
                parent,
                used=(),
                cited=("#a1b2c3",),
                citation_only=(),
                impact_codes=(),
                occurred_at=NOW,
            )

        event = build_usage_attestation_event(
            parent,
            used=(),
            cited=("#a1b2c3",),
            citation_only=("#a1b2c3",),
            impact_codes=(),
            occurred_at=NOW,
        )
        self.assertEqual(event["payload"]["citation_only"], ["#a1b2c3"])

    def test_malformed_attestation_lists_raise_stable_integrity_errors(self) -> None:
        parent = build_context_event(context_metadata(), occurred_at=NOW)
        event = build_usage_attestation_event(
            parent,
            used=(),
            cited=(),
            citation_only=(),
            impact_codes=(),
            occurred_at=NOW,
        )
        event["payload"]["used"] = [{}]

        with self.assertRaises(EventIntegrityError) as raised:
            validate_event(event)

        self.assertEqual(raised.exception.code, "event_schema_invalid")

    def test_generic_append_cannot_bypass_attestation_parent_lookup(self) -> None:
        parent = build_context_event(context_metadata(), occurred_at=NOW)
        event = build_usage_attestation_event(
            parent,
            used=(),
            cited=(),
            citation_only=(),
            impact_codes=(),
            occurred_at=NOW,
        )

        with self.assertRaises(EventIntegrityError) as raised:
            append_event(event, state_dir=self.state_dir, project_root=self.repo)

        self.assertEqual(
            raised.exception.code, "usage_attestation_requires_parent_lookup"
        )
        self.assertFalse(any(self.state_dir.rglob("*.jsonl")))

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

    def test_complete_malformed_final_line_is_not_treated_as_truncation(self) -> None:
        event = build_context_event(context_metadata(), occurred_at=NOW)
        event_path = append_event(
            event,
            state_dir=self.state_dir,
            project_root=self.repo,
        )
        with event_path.open("a", encoding="utf-8") as stream:
            stream.write('{"schema_version":1,broken}\n')

        with self.assertRaises(EventIntegrityError) as raised:
            read_event_file(event_path)

        self.assertEqual(raised.exception.code, "event_log_corrupt")

    def test_duplicate_json_keys_are_rejected_instead_of_silently_overwritten(self) -> None:
        event = build_context_event(context_metadata(), occurred_at=NOW)
        event_path = append_event(
            event,
            state_dir=self.state_dir,
            project_root=self.repo,
        )
        serialized = json.dumps(event, separators=(",", ":"))
        duplicated = serialized.replace(
            '"project_id":"skillz-claude"',
            '"project_id":"private-shadow","project_id":"skillz-claude"',
            1,
        )
        event_path.write_text(duplicated + "\n", encoding="utf-8")

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
