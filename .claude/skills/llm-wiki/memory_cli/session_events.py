"""Relationship-aware append workflows for ``memory finish``."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

from . import events as event_store
from .conflicts import (
    build_memory_conflict_event,
    build_memory_debt_action_event,
    validate_repository_evidence_path,
)
from .contracts import (
    ConflictCategory,
    ConflictEvidenceType,
    ConflictRisk,
    DEBT_ACTION_POLICY_VERSION,
    DebtAction,
)


@dataclass(frozen=True, slots=True)
class UsageAttestationResult:
    parent_event: dict[str, Any]
    event: dict[str, Any]
    diagnostics: tuple[dict[str, str], ...] = ()
    conflict_event: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class DebtActionResult:
    parent_event: dict[str, Any]
    event: dict[str, Any]
    diagnostics: tuple[dict[str, str], ...] = ()


def append_usage_attestation(
    *,
    project_id: str,
    parent_event_id: str,
    used: Sequence[str],
    cited: Sequence[str],
    citation_only: Sequence[str],
    impact_codes: Sequence[str],
    conflict_docid: str | None = None,
    repository_path: str | None = None,
    evidence_type: ConflictEvidenceType | None = None,
    conflict_category: ConflictCategory | None = None,
    conflict_risk: ConflictRisk | None = None,
    prepare_debt: bool = False,
    state_dir: Path | None = None,
    project_root: Path | None = None,
    occurred_at: datetime | None = None,
) -> UsageAttestationResult:
    """Append one attestation and optional conflict under one project lock."""

    if not event_store._PROJECT_ID.fullmatch(project_id):
        raise event_store._error(
            "event_schema_invalid",
            "Attestation project ID is invalid.",
            "Use the project ID from the nearest validated memory manifest.",
        )
    if not event_store._CONTEXT_EVENT_ID.fullmatch(parent_event_id):
        raise event_store._error(
            "parent_event_invalid",
            "Parent event ID must identify a context_completed event.",
            "Use the event_id returned by memory context.",
        )
    root = event_store.validate_state_directory(
        state_dir or event_store.resolve_state_dir(), project_root
    )
    project_dir = event_store._project_directory(root, project_id)
    lock_path = root / "events" / f".{project_id}.lock"
    try:
        event_store.ensure_private_state_directory(root)
        with event_store._project_lock(lock_path):
            parents: list[dict[str, Any]] = []
            attestations: list[dict[str, Any]] = []
            conflicts: list[dict[str, Any]] = []
            diagnostics: list[dict[str, str]] = []
            if project_dir.exists():
                for path in sorted(project_dir.glob("*.jsonl")):
                    result = event_store.read_event_file(path)
                    diagnostics.extend(result.diagnostics)
                    for stored_event in result.events:
                        if stored_event["event_id"] == parent_event_id:
                            parents.append(stored_event)
                        if (
                            stored_event["event_type"]
                            == event_store.EVENT_TYPE_USAGE_ATTESTED
                            and stored_event["parent_event_id"] == parent_event_id
                        ):
                            attestations.append(stored_event)
                        if (
                            stored_event["event_type"]
                            == event_store.EVENT_TYPE_MEMORY_CONFLICT
                            and stored_event["parent_event_id"] == parent_event_id
                        ):
                            conflicts.append(stored_event)
            if diagnostics:
                raise event_store._error(
                    "event_log_truncated",
                    "The project event log has an incomplete final line.",
                    "Run memory purge before appending an attestation.",
                )
            if not parents:
                raise event_store._error(
                    "parent_event_not_found",
                    f"Parent context event was not found: {parent_event_id}.",
                    "Use a retained event_id from memory context in the current project.",
                )
            if len(parents) != 1:
                raise event_store._error(
                    "parent_event_ambiguous",
                    f"Parent context event is duplicated: {parent_event_id}.",
                    "Inspect or purge the affected local project telemetry.",
                )
            conflict_values = (
                conflict_docid,
                repository_path,
                evidence_type,
                conflict_category,
                conflict_risk,
            )
            has_conflict = any(value is not None for value in conflict_values)
            if has_conflict and not all(value is not None for value in conflict_values):
                raise event_store._error(
                    "conflict_arguments_incomplete",
                    "Conflict declaration requires docid, repository evidence, type, category and risk.",
                    "Provide every documented --conflict-* option together.",
                )
            if prepare_debt and not has_conflict:
                raise event_store._error(
                    "conflict_arguments_incomplete",
                    "An open debt requires a declared memory conflict.",
                    "Use --prepare-debt together with every --conflict-* option.",
                )
            finish_time = occurred_at or event_store._utc_now()
            event = event_store.build_usage_attestation_event(
                parents[0],
                used=used,
                cited=cited,
                citation_only=citation_only,
                impact_codes=impact_codes,
                occurred_at=finish_time,
            )
            conflict_event: dict[str, object] | None = None
            if has_conflict:
                assert conflict_docid is not None
                assert repository_path is not None
                assert evidence_type is not None
                assert conflict_category is not None
                assert conflict_risk is not None
                conflict_event = build_memory_conflict_event(
                    parents[0],
                    memory_docid=conflict_docid,
                    repository_path=repository_path,
                    evidence_type=evidence_type,
                    category=conflict_category,
                    risk=conflict_risk,
                    prepare_debt=prepare_debt,
                    occurred_at=finish_time,
                )
            if attestations:
                if not has_conflict:
                    if (
                        len(attestations) == 1
                        and not conflicts
                        and attestations[0]["payload"] == event["payload"]
                    ):
                        replay_diagnostics = event_store.fsync_state_directory(project_dir)
                        if replay_diagnostics:
                            return UsageAttestationResult(
                                parents[0],
                                attestations[0],
                                diagnostics=replay_diagnostics,
                            )
                    raise event_store._error(
                        "parent_already_attested",
                        f"Parent context event is already attested: {parent_event_id}.",
                        "Reuse the existing immutable attestation instead of appending another.",
                    )
                valid_replay_shape = (
                    len(attestations) == 1
                    and len(conflicts) == 1
                    and conflict_event is not None
                )
                if not valid_replay_shape:
                    raise event_store._error(
                        "parent_already_attested",
                        f"Parent context event is already attested: {parent_event_id}.",
                        "Reuse the existing immutable attestation instead of appending another.",
                    )
                conflict_mismatch = bool(
                    has_conflict
                    and conflict_event is not None
                    and conflicts[0]["payload"] != conflict_event["payload"]
                )
                if attestations[0]["payload"] != event["payload"] or conflict_mismatch:
                    raise event_store._error(
                        "finish_replay_mismatch",
                        "Stored finish events do not match the requested immutable replay.",
                        "Retry with the original structured finish arguments.",
                    )
                replay_diagnostics = event_store.fsync_state_directory(project_dir)
                return UsageAttestationResult(
                    parents[0],
                    attestations[0],
                    diagnostics=replay_diagnostics,
                    conflict_event=conflicts[0] if conflicts else None,
                )
            if conflicts:
                raise event_store._error(
                    "parent_already_conflicted",
                    f"Parent context event already has a conflict: {parent_event_id}.",
                    "Inspect the inconsistent local event chain before retrying.",
                )
            events_to_append = [event]
            batch_diagnostics: tuple[dict[str, str], ...] = ()
            if conflict_event is not None:
                validate_repository_evidence_path(
                    repository_path,
                    project_root=project_root,
                )
                events_to_append.append(conflict_event)
                batch_diagnostics = event_store.append_event_batch_atomically(
                    event_store._event_path(project_dir, event),
                    events_to_append,
                )
            else:
                batch_diagnostics = event_store._append_event_line(
                    event_store._event_path(project_dir, event), event
                )
    except OSError as error:
        raise event_store._error(
            "event_store_unavailable",
            "The usage attestation could not be persisted safely.",
            "Restore access to the private memory state directory, then retry.",
        ) from error
    return UsageAttestationResult(
        parents[0],
        event,
        diagnostics=batch_diagnostics,
        conflict_event=conflict_event,
    )


def append_memory_debt_action(
    *,
    project_id: str,
    parent_event_id: str,
    action: DebtAction,
    reason: str | None,
    snooze_until: str | None,
    state_dir: Path | None = None,
    project_root: Path | None = None,
    occurred_at: datetime | None = None,
) -> DebtActionResult:
    """Validate and append one review action under the project lock."""

    if not event_store._PROJECT_ID.fullmatch(project_id):
        raise event_store._error(
            "event_schema_invalid",
            "Debt action project ID is invalid.",
            "Use the project ID from the nearest validated memory manifest.",
        )
    if not event_store._CONFLICT_EVENT_ID.fullmatch(parent_event_id):
        raise event_store._error(
            "parent_event_invalid",
            "Debt action parent must identify a memory_conflict event.",
            "Use an open debt ID returned by memory finish.",
        )
    root = event_store.validate_state_directory(
        state_dir or event_store.resolve_state_dir(), project_root
    )
    project_dir = event_store._project_directory(root, project_id)
    lock_path = root / "events" / f".{project_id}.lock"
    try:
        event_store.ensure_private_state_directory(root)
        with event_store._project_lock(lock_path):
            parents: list[dict[str, Any]] = []
            reviewed_actions: list[dict[str, Any]] = []
            diagnostics: list[dict[str, str]] = []
            if project_dir.exists():
                for path in sorted(project_dir.glob("*.jsonl")):
                    result = event_store.read_event_file(path)
                    diagnostics.extend(result.diagnostics)
                    for stored_event in result.events:
                        if stored_event["event_id"] == parent_event_id:
                            parents.append(stored_event)
                        if (
                            stored_event["event_type"]
                            == event_store.EVENT_TYPE_MEMORY_DEBT_ACTION
                            and stored_event["parent_event_id"] == parent_event_id
                        ):
                            reviewed_actions.append(stored_event)
            if diagnostics:
                raise event_store._error(
                    "event_log_truncated",
                    "The project event log has an incomplete final line.",
                    "Run memory purge before appending a debt action.",
                )
            if not parents:
                raise event_store._error(
                    "parent_event_not_found",
                    f"Open debt event was not found: {parent_event_id}.",
                    "Use a retained debt ID from memory finish in the current project.",
                )
            if len(parents) != 1:
                raise event_store._error(
                    "parent_event_ambiguous",
                    f"Open debt event is duplicated: {parent_event_id}.",
                    "Inspect or purge the affected local project telemetry.",
                )
            if reviewed_actions:
                requested_payload = {
                    "debt_action_policy_version": DEBT_ACTION_POLICY_VERSION,
                    "action": action.value,
                    "reason": reason,
                    "snooze_until": snooze_until,
                }
                if (
                    len(reviewed_actions) == 1
                    and reviewed_actions[0]["payload"] == requested_payload
                ):
                    replay_diagnostics = event_store.fsync_state_directory(project_dir)
                    if replay_diagnostics:
                        return DebtActionResult(
                            parents[0],
                            reviewed_actions[0],
                            diagnostics=replay_diagnostics,
                        )
                raise event_store._error(
                    "debt_already_reviewed",
                    f"Memory debt is already reviewed: {parent_event_id}.",
                    "Reuse the existing immutable debt action.",
                )
            event = build_memory_debt_action_event(
                parents[0],
                action=action,
                reason=reason,
                snooze_until=snooze_until,
                occurred_at=occurred_at,
            )
            append_diagnostics = event_store._append_event_line(
                event_store._event_path(project_dir, event), event
            )
    except OSError as error:
        raise event_store._error(
            "event_store_unavailable",
            "The memory debt action could not be persisted safely.",
            "Restore access to the private memory state directory, then retry.",
        ) from error
    return DebtActionResult(parents[0], event, diagnostics=append_diagnostics)
