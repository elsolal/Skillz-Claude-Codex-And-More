"""Closed metadata-only policy for repository-first memory conflicts."""

from __future__ import annotations

import re
from datetime import date, datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from .contracts import (
    CONFLICT_POLICY_VERSION,
    DEBT_ACTION_POLICY_VERSION,
    ConflictCategory,
    ConflictEvidenceType,
    ConflictRisk,
    DebtAction,
)
from .events import EventIntegrityError


PRECEDENCE_REPOSITORY = "repository"
CONFLICT_NEXT_ACTIONS = ("continue", "inspect", "prepare_patch")
BLOCKING_CATEGORIES = frozenset(
    {
        ConflictCategory.PRODUCT,
        ConflictCategory.ARCHITECTURE,
        ConflictCategory.SECURITY,
        ConflictCategory.DATA,
    }
)

_DOCID = re.compile(r"^#[A-Za-z0-9._:-]+$")
_REASON_SLUG = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_WINDOWS_ABSOLUTE_PATH = re.compile(r"^[A-Za-z]:[\\/]")
_CONFLICT_PAYLOAD_KEYS = (
    "conflict_policy_version",
    "risk",
    "category",
    "precedence",
    "requires_human",
    "memory",
    "repository",
    "debt",
    "next_actions",
)
_MEMORY_REFERENCE_KEYS = ("docid", "path")
_REPOSITORY_REFERENCE_KEYS = ("path", "evidence_type")
_DEBT_DRAFT_KEYS = ("status", "draft")
_DEBT_ACTION_PAYLOAD_KEYS = (
    "debt_action_policy_version",
    "action",
    "reason",
    "snooze_until",
)


def _error(code: str, message: str, correction: str) -> EventIntegrityError:
    return EventIntegrityError(code=code, message=message, correction=correction)


def _exact_keys(
    value: Mapping[str, object], expected: tuple[str, ...], field: str
) -> None:
    if len(value) != len(expected) or set(value) != set(expected):
        raise _error(
            "event_schema_invalid",
            f"{field} does not match the closed metadata-only schema.",
            "Remove unknown fields and rebuild the conflict through memory finish.",
        )


def normalize_relative_path(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise _error(
            "event_schema_invalid",
            f"{field} must be a non-empty relative path.",
            "Use a normalized POSIX path relative to its declared root.",
        )
    normalized = PurePosixPath(value)
    if (
        value == "."
        or "\\" in value
        or value.startswith("//")
        or _WINDOWS_ABSOLUTE_PATH.match(value)
        or normalized.is_absolute()
        or ".." in normalized.parts
        or value != normalized.as_posix()
    ):
        raise _error(
            "event_schema_invalid",
            f"{field} must be a normalized relative POSIX path.",
            "Remove absolute roots and traversal from the evidence reference.",
        )
    return normalized.as_posix()


def validate_repository_evidence_path(
    value: object, *, project_root: Path | None
) -> str:
    """Require one existing regular repository file without symlink escape."""

    normalized = normalize_relative_path(value, field="conflict.repository.path")
    if project_root is None:
        raise _error(
            "repository_evidence_unverifiable",
            "Repository evidence requires the current project root.",
            "Declare conflicts through memory finish from an activated repository.",
        )
    try:
        canonical_root = project_root.resolve(strict=True)
        candidate = project_root.joinpath(*PurePosixPath(normalized).parts)
        canonical_candidate = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise _error(
            "repository_evidence_not_found",
            f"Repository evidence does not identify an existing file: {normalized}.",
            "Reference an existing regular file inside the current repository.",
        ) from error
    if (
        canonical_root not in canonical_candidate.parents
        or not canonical_candidate.is_file()
    ):
        raise _error(
            "repository_evidence_invalid",
            f"Repository evidence is not a regular file inside the project: {normalized}.",
            "Reference an existing regular file that resolves within the repository.",
        )
    return normalized


def requires_human(*, category: ConflictCategory, risk: ConflictRisk) -> bool:
    return risk is ConflictRisk.HIGH and category in BLOCKING_CATEGORIES


def build_conflict_payload(
    parent_event: Mapping[str, object],
    *,
    memory_docid: str,
    repository_path: str,
    evidence_type: ConflictEvidenceType,
    category: ConflictCategory,
    risk: ConflictRisk,
    prepare_debt: bool,
) -> dict[str, object]:
    if not _DOCID.fullmatch(memory_docid):
        raise _error(
            "conflict_docid_invalid",
            "Conflict memory evidence must use a normalized QMD docid.",
            "Use a docid returned by the parent memory context event.",
        )
    payload = parent_event.get("payload")
    if not isinstance(payload, Mapping):
        raise _error(
            "parent_event_invalid",
            "Conflict declaration requires a valid context parent payload.",
            "Use the event_id returned by memory context.",
        )
    retrieved = payload.get("retrieved")
    if not isinstance(retrieved, list):
        raise _error(
            "parent_event_invalid",
            "Conflict declaration requires measured retrieved evidence.",
            "Use the event_id returned by memory context.",
        )
    matches = [
        hit
        for hit in retrieved
        if isinstance(hit, Mapping) and hit.get("docid") == memory_docid
    ]
    if len(matches) != 1:
        raise _error(
            "conflict_docid_not_retrieved",
            f"Conflict docid was not uniquely retrieved by the parent: {memory_docid}.",
            "Declare exactly one docid present in the parent context event.",
        )
    memory_path = normalize_relative_path(
        matches[0].get("path"), field="conflict.memory.path"
    )
    repository_reference = normalize_relative_path(
        repository_path, field="conflict.repository.path"
    )
    result: dict[str, object] = {
        "conflict_policy_version": CONFLICT_POLICY_VERSION,
        "risk": risk.value,
        "category": category.value,
        "precedence": PRECEDENCE_REPOSITORY,
        "requires_human": requires_human(category=category, risk=risk),
        "memory": {"docid": memory_docid, "path": memory_path},
        "repository": {
            "path": repository_reference,
            "evidence_type": evidence_type.value,
        },
        "debt": (
            {"status": "open", "draft": "metadata_only"}
            if prepare_debt
            else None
        ),
        "next_actions": list(CONFLICT_NEXT_ACTIONS),
    }
    validate_conflict_payload(result)
    return result


def build_memory_conflict_event(
    parent_event: Mapping[str, object],
    *,
    memory_docid: str,
    repository_path: str,
    evidence_type: ConflictEvidenceType,
    category: ConflictCategory,
    risk: ConflictRisk,
    prepare_debt: bool,
    occurred_at: datetime | None = None,
    event_id: str | None = None,
) -> dict[str, object]:
    """Build one repository-first conflict linked to measured context."""

    from . import events as event_store

    event_store.validate_event(parent_event)
    if parent_event["event_type"] != event_store.EVENT_TYPE_CONTEXT_COMPLETED:
        raise _error(
            "parent_event_invalid",
            "Memory conflicts require a context_completed parent.",
            "Use the event_id returned by memory context.",
        )
    timestamp = event_store._as_utc(occurred_at or event_store._utc_now())
    event: dict[str, object] = {
        "schema_version": event_store.EVENT_SCHEMA_VERSION,
        "event_id": event_id or event_store._new_event_id(timestamp, prefix="con"),
        "event_type": event_store.EVENT_TYPE_MEMORY_CONFLICT,
        "occurred_at": event_store._format_time(timestamp),
        "project_id": parent_event["project_id"],
        "parent_event_id": parent_event["event_id"],
        "payload": build_conflict_payload(
            parent_event,
            memory_docid=memory_docid,
            repository_path=repository_path,
            evidence_type=evidence_type,
            category=category,
            risk=risk,
            prepare_debt=prepare_debt,
        ),
    }
    event_store.validate_event(event)
    return event


def validate_conflict_payload(payload: Mapping[str, object]) -> None:
    _exact_keys(payload, _CONFLICT_PAYLOAD_KEYS, "event.payload")
    if payload["conflict_policy_version"] != CONFLICT_POLICY_VERSION:
        raise _error(
            "event_schema_invalid",
            "Unknown conflict policy version.",
            f"Use {CONFLICT_POLICY_VERSION} for V1 memory conflicts.",
        )
    try:
        risk = ConflictRisk(payload["risk"])
        category = ConflictCategory(payload["category"])
    except (TypeError, ValueError) as error:
        raise _error(
            "event_schema_invalid",
            "Conflict risk or category is invalid.",
            "Use the documented conflict risk and category values.",
        ) from error
    if payload["precedence"] != PRECEDENCE_REPOSITORY:
        raise _error(
            "event_schema_invalid",
            "Repository evidence must have operational precedence.",
            "Use precedence repository for memory conflicts.",
        )
    if payload["requires_human"] is not requires_human(category=category, risk=risk):
        raise _error(
            "event_schema_invalid",
            "requires_human does not match the conflict risk matrix.",
            "Derive requires_human through the conflict-v1 policy.",
        )
    memory = payload["memory"]
    repository = payload["repository"]
    if not isinstance(memory, Mapping) or not isinstance(repository, Mapping):
        raise _error(
            "event_schema_invalid",
            "Conflict evidence references must be objects.",
            "Build both references through memory finish.",
        )
    _exact_keys(memory, _MEMORY_REFERENCE_KEYS, "event.payload.memory")
    _exact_keys(repository, _REPOSITORY_REFERENCE_KEYS, "event.payload.repository")
    if not isinstance(memory["docid"], str) or not _DOCID.fullmatch(memory["docid"]):
        raise _error(
            "event_schema_invalid",
            "Conflict memory docid is invalid.",
            "Use a normalized QMD docid from the parent event.",
        )
    normalize_relative_path(memory["path"], field="event.payload.memory.path")
    normalize_relative_path(repository["path"], field="event.payload.repository.path")
    try:
        ConflictEvidenceType(repository["evidence_type"])
    except (TypeError, ValueError) as error:
        raise _error(
            "event_schema_invalid",
            "Conflict repository evidence type is invalid.",
            "Use a documented structured evidence type.",
        ) from error
    debt = payload["debt"]
    if debt is not None:
        if not isinstance(debt, Mapping):
            raise _error(
                "event_schema_invalid",
                "Conflict debt draft must be an object or null.",
                "Prepare a metadata-only open debt through memory finish.",
            )
        _exact_keys(debt, _DEBT_DRAFT_KEYS, "event.payload.debt")
        if debt != {"status": "open", "draft": "metadata_only"}:
            raise _error(
                "event_schema_invalid",
                "Conflict debt draft does not match the V1 open metadata-only form.",
                "Use status open and draft metadata_only.",
            )
    if payload["next_actions"] != list(CONFLICT_NEXT_ACTIONS):
        raise _error(
            "event_schema_invalid",
            "Conflict next actions do not match the V1 contract.",
            "Use continue, inspect and prepare_patch in canonical order.",
        )


def validate_debt_action(
    *,
    action: DebtAction,
    reason: str | None,
    snooze_until: str | None,
    today: date | None = None,
) -> dict[str, str | None]:
    if action is DebtAction.FIX:
        valid = reason is None and snooze_until is None
    elif action is DebtAction.IGNORE:
        valid = (
            isinstance(reason, str)
            and _REASON_SLUG.fullmatch(reason) is not None
            and snooze_until is None
        )
    else:
        valid = reason is None and snooze_until is not None
        if valid:
            try:
                parsed = date.fromisoformat(snooze_until)
            except (TypeError, ValueError):
                valid = False
            else:
                valid = parsed > (today or datetime.now(timezone.utc).date())
    if not valid:
        raise _error(
            "debt_action_invalid",
            "Debt action arguments do not match the closed metadata-only contract.",
            "Use fix alone, ignore with a reason slug, or snooze with a future YYYY-MM-DD date.",
        )
    return {
        "action": action.value,
        "reason": reason,
        "snooze_until": snooze_until,
    }


def build_debt_action_payload(
    *, action: DebtAction, reason: str | None, snooze_until: str | None
) -> dict[str, object]:
    validated = validate_debt_action(
        action=action,
        reason=reason,
        snooze_until=snooze_until,
    )
    result: dict[str, object] = {
        "debt_action_policy_version": DEBT_ACTION_POLICY_VERSION,
        **validated,
    }
    validate_debt_action_payload(result)
    return result


def build_memory_debt_action_event(
    parent_event: Mapping[str, object],
    *,
    action: DebtAction,
    reason: str | None,
    snooze_until: str | None,
    occurred_at: datetime | None = None,
    event_id: str | None = None,
) -> dict[str, object]:
    """Build one immutable review action for an open conflict debt."""

    from . import events as event_store

    event_store.validate_event(parent_event)
    if parent_event["event_type"] != event_store.EVENT_TYPE_MEMORY_CONFLICT:
        raise _error(
            "parent_event_invalid",
            "Debt actions require a memory_conflict parent.",
            "Use an open debt ID returned by memory finish.",
        )
    parent_payload = parent_event["payload"]
    assert isinstance(parent_payload, Mapping)
    if parent_payload["debt"] is None:
        raise _error(
            "debt_not_open",
            "The memory conflict did not prepare an open debt.",
            "Declare the conflict with --prepare-debt before reviewing it.",
        )
    timestamp = event_store._as_utc(occurred_at or event_store._utc_now())
    event: dict[str, object] = {
        "schema_version": event_store.EVENT_SCHEMA_VERSION,
        "event_id": event_id or event_store._new_event_id(timestamp, prefix="deb"),
        "event_type": event_store.EVENT_TYPE_MEMORY_DEBT_ACTION,
        "occurred_at": event_store._format_time(timestamp),
        "project_id": parent_event["project_id"],
        "parent_event_id": parent_event["event_id"],
        "payload": build_debt_action_payload(
            action=action,
            reason=reason,
            snooze_until=snooze_until,
        ),
    }
    event_store.validate_event(event)
    return event


def validate_debt_action_payload(payload: Mapping[str, object]) -> None:
    _exact_keys(payload, _DEBT_ACTION_PAYLOAD_KEYS, "event.payload")
    if payload["debt_action_policy_version"] != DEBT_ACTION_POLICY_VERSION:
        raise _error(
            "event_schema_invalid",
            "Unknown debt action policy version.",
            f"Use {DEBT_ACTION_POLICY_VERSION} for V1 debt actions.",
        )
    try:
        action = DebtAction(payload["action"])
    except (TypeError, ValueError) as error:
        raise _error(
            "event_schema_invalid",
            "Debt action is invalid.",
            "Use fix, ignore or snooze.",
        ) from error
    validate_debt_action(
        action=action,
        reason=payload["reason"] if isinstance(payload["reason"], str) else None,
        snooze_until=(
            payload["snooze_until"]
            if isinstance(payload["snooze_until"], str)
            else None
        ),
        today=date.min,
    )
    if payload["reason"] is not None and not isinstance(payload["reason"], str):
        raise _error(
            "event_schema_invalid",
            "Debt action reason must be a structured slug or null.",
            "Use --reason only with ignore.",
        )
    if payload["snooze_until"] is not None and not isinstance(
        payload["snooze_until"], str
    ):
        raise _error(
            "event_schema_invalid",
            "Debt snooze date must be YYYY-MM-DD or null.",
            "Use --until only with snooze.",
        )
