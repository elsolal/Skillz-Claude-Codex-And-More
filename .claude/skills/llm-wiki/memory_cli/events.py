"""Metadata-only context events, private JSONL storage, and retention."""

from __future__ import annotations

import json
import os
import re
import tempfile
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterator, Mapping, Sequence

from .contracts import IMPACT_TAXONOMY_VERSION, ImpactCode


EVENT_SCHEMA_VERSION = 1
EVENT_TYPE_CONTEXT_COMPLETED = "context_completed"
EVENT_TYPE_USAGE_ATTESTED = "usage_attested"
EVENT_EXIT_CODE = 50

_CONTEXT_ROOT_KEYS = (
    "schema_version",
    "event_id",
    "event_type",
    "occurred_at",
    "project_id",
    "payload",
)
_ATTESTATION_ROOT_KEYS = (
    "schema_version",
    "event_id",
    "event_type",
    "occurred_at",
    "project_id",
    "parent_event_id",
    "payload",
)
_CONTEXT_PAYLOAD_KEYS = (
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
)
_ATTESTATION_PAYLOAD_KEYS = (
    "impact_taxonomy_version",
    "used",
    "cited",
    "citation_only",
    "impact_codes",
)
_RETRIEVED_KEYS = ("docid", "collection", "path", "score")
_READ_KEYS = ("docid", "collection", "path")

_PROJECT_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
_CONTEXT_EVENT_ID = re.compile(r"^mem_\d{8}T\d{12}Z_[0-9a-f]{16}$")
_ATTESTATION_EVENT_ID = re.compile(r"^att_\d{8}T\d{12}Z_[0-9a-f]{16}$")
_DOCID = re.compile(r"^#[A-Za-z0-9._:-]+$")
_WINDOWS_ABSOLUTE_PATH = re.compile(r"^[A-Za-z]:[\\/]")
_SENSITIVE_KEY = re.compile(
    r"(?:^|_)(?:api[_-]?key|access[_-]?token|authorization|cookie|credential|"
    r"password|passwd|private[_-]?key|secret)(?:$|_)",
    re.IGNORECASE,
)
_CONTENT_KEYS = {
    "body",
    "content",
    "prompt",
    "query",
    "response",
    "snippet",
    "transcript",
}
_SECRET_VALUES = (
    re.compile(r"^sk-(?:proj-)?[A-Za-z0-9_-]{20,}$"),
    re.compile(r"^gh[pousr]_[A-Za-z0-9]{20,}$"),
    re.compile(r"^AKIA[0-9A-Z]{16}$"),
    re.compile(r"^eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$"),
    re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----"),
)

_MODES = {"minimal", "project", "historical"}
_TASK_CATEGORIES = {
    "bug",
    "architecture",
    "product",
    "operations",
    "security",
    "data",
    "historical",
    "onboarding",
    "general",
}
_STATUSES = {"sufficient", "insufficient", "ambiguous", "blocked", "degraded"}
_FRESHNESS = {"fresh", "stale", "unknown"}
_FALLBACK_REASONS = {
    "no_result",
    "below_score",
    "insufficient_coverage",
    "stale",
    "missing_provenance",
    "task_requires_transverse",
    "ambiguous",
}
_RISK_REASONS = {"security", "data", "architecture", "product", "incident"}


class EventIntegrityError(RuntimeError):
    """A stable telemetry/privacy failure that always maps to exit 50."""

    exit_code = EVENT_EXIT_CODE

    def __init__(self, *, code: str, message: str, correction: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.correction = correction

    def as_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "message": self.message,
            "correction": self.correction,
        }


@dataclass(frozen=True, slots=True)
class EventReadResult:
    events: tuple[dict[str, Any], ...]
    diagnostics: tuple[dict[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class UsageAttestationResult:
    parent_event: dict[str, Any]
    event: dict[str, Any]
    diagnostics: tuple[dict[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class PurgeOutcome:
    project_id: str
    retention_days: int
    force: bool
    deleted_events: int
    retained_events: int
    removed_files: int
    corrupted_files: int

    def data(self) -> dict[str, object]:
        return {
            "retention_days": self.retention_days,
            "force": self.force,
            "deleted_events": self.deleted_events,
            "retained_events": self.retained_events,
            "removed_files": self.removed_files,
            "corrupted_files": self.corrupted_files,
        }


def _error(code: str, message: str, correction: str) -> EventIntegrityError:
    return EventIntegrityError(code=code, message=message, correction=correction)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise _error(
            "event_time_invalid",
            "Event timestamps must include a timezone.",
            "Use a timezone-aware UTC datetime.",
        )
    return value.astimezone(timezone.utc)


def _format_time(value: datetime) -> str:
    utc = _as_utc(value)
    if utc.microsecond:
        return utc.isoformat(timespec="microseconds").replace("+00:00", "Z")
    return utc.isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_time(value: object) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise _error(
            "event_time_invalid",
            "Event occurred_at must be an ISO-8601 UTC string.",
            "Rebuild the event through build_context_event().",
        )
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise _error(
            "event_time_invalid",
            "Event occurred_at is not valid ISO-8601.",
            "Rebuild the event through build_context_event().",
        ) from error
    return _as_utc(parsed)


def _new_event_id(occurred_at: datetime, *, prefix: str = "mem") -> str:
    timestamp = _as_utc(occurred_at).strftime("%Y%m%dT%H%M%S%fZ")
    return f"{prefix}_{timestamp}_{uuid.uuid4().hex[:16]}"


def _expect_exact_keys(value: Mapping[str, object], expected: Sequence[str], field: str) -> None:
    if len(value) != len(expected) or set(value) != set(expected):
        raise _error(
            "event_schema_invalid",
            f"{field} does not match the closed metadata-only schema.",
            "Remove unknown fields and build the event through the V1 event contract.",
        )


def _expect_string(value: object, field: str, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value:
        raise _error(
            "event_schema_invalid",
            f"{field} must be a non-empty string.",
            "Build the event through the V1 event contract.",
        )
    return value


def _expect_non_negative_int(value: object, field: str, *, nullable: bool = False) -> int | None:
    if value is None and nullable:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise _error(
            "event_schema_invalid",
            f"{field} must be a non-negative integer.",
            "Build the event through the V1 event contract.",
        )
    return value


def _scan_privacy(value: object, *, field: str = "event") -> None:
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            if not isinstance(raw_key, str):
                raise _error(
                    "event_privacy_violation",
                    "Event keys must be strings from the metadata-only allowlist.",
                    "Remove the non-string event key.",
                )
            normalized = raw_key.lower().replace("-", "_")
            if normalized in _CONTENT_KEYS or _SENSITIVE_KEY.search(normalized):
                raise _error(
                    "event_privacy_violation",
                    f"Event field {raw_key!r} is forbidden by the metadata-only contract.",
                    "Remove content-bearing and sensitive fields before append.",
                )
            _scan_privacy(child, field=f"{field}.{raw_key}")
        return
    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _scan_privacy(child, field=f"{field}[{index}]")
        return
    if isinstance(value, str):
        if value.startswith("/") or value.startswith("\\\\") or _WINDOWS_ABSOLUTE_PATH.match(value):
            raise _error(
                "event_privacy_violation",
                f"{field} contains an absolute path.",
                "Store only normalized paths relative to the declared memory root.",
            )
        if any(pattern.search(value) for pattern in _SECRET_VALUES):
            raise _error(
                "event_privacy_violation",
                f"{field} contains a secret-shaped value.",
                "Remove credentials and secret material before append.",
            )


def _strict_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate event key: {key}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")


def _validate_relative_path(value: object, field: str) -> None:
    path = _expect_string(value, field)
    assert path is not None
    normalized = PurePosixPath(path)
    if (
        path == "."
        or "\\" in path
        or normalized.is_absolute()
        or ".." in normalized.parts
        or path != normalized.as_posix()
    ):
        raise _error(
            "event_schema_invalid",
            f"{field} must be a normalized relative POSIX path.",
            "Store a path relative to the declared memory root without traversal.",
        )


def _ordered_unique(values: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _validate_docid_list(value: object, field: str) -> list[str]:
    if not isinstance(value, list):
        raise _error(
            "event_schema_invalid",
            f"{field} must be a docid list.",
            "Use repeated CLI options with normalized QMD docids.",
        )
    if len(value) != len(set(value)):
        raise _error(
            "event_schema_invalid",
            f"{field} must not contain duplicate docids.",
            "Deduplicate the attested docids before append.",
        )
    for docid in value:
        if not isinstance(docid, str) or not _DOCID.fullmatch(docid):
            raise _error(
                "event_schema_invalid",
                f"{field} contains an invalid docid.",
                "Use normalized QMD docids beginning with #.",
            )
    return value


def _validate_attestation_payload(payload: Mapping[str, object]) -> None:
    _expect_exact_keys(payload, _ATTESTATION_PAYLOAD_KEYS, "event.payload")
    if payload["impact_taxonomy_version"] != IMPACT_TAXONOMY_VERSION:
        raise _error(
            "event_schema_invalid",
            "Unknown impact taxonomy version.",
            f"Use {IMPACT_TAXONOMY_VERSION} for V1 usage attestations.",
        )
    used = set(_validate_docid_list(payload["used"], "event.payload.used"))
    cited = set(_validate_docid_list(payload["cited"], "event.payload.cited"))
    citation_only = set(
        _validate_docid_list(payload["citation_only"], "event.payload.citation_only")
    )
    if not citation_only <= cited:
        invalid = sorted(citation_only - cited)
        raise _error(
            "citation_only_not_cited",
            f"citation_only docids must also be cited: {', '.join(invalid)}.",
            "Add each citation-only docid to --cited.",
        )
    unjustified = cited - used - citation_only
    if unjustified:
        raise _error(
            "citation_not_used",
            f"Cited docids must be used or marked citation_only: {', '.join(sorted(unjustified))}.",
            "Add the docid to --used or justify it with --citation-only.",
        )
    impact_codes = payload["impact_codes"]
    allowed_impacts = {code.value for code in ImpactCode}
    if (
        not isinstance(impact_codes, list)
        or len(impact_codes) != len(set(impact_codes))
        or not all(isinstance(code, str) and code in allowed_impacts for code in impact_codes)
    ):
        raise _error(
            "event_schema_invalid",
            "Impact codes must be a unique impact-v1 code list.",
            "Use a documented impact-v1 code or leave impact codes empty.",
        )


def validate_event(event: Mapping[str, object]) -> None:
    """Reject any field or value outside the closed metadata-only V1 contract."""

    _scan_privacy(event)
    event_type = event.get("event_type")
    if event_type == EVENT_TYPE_CONTEXT_COMPLETED:
        _expect_exact_keys(event, _CONTEXT_ROOT_KEYS, "event")
        event_id_pattern = _CONTEXT_EVENT_ID
    elif event_type == EVENT_TYPE_USAGE_ATTESTED:
        _expect_exact_keys(event, _ATTESTATION_ROOT_KEYS, "event")
        event_id_pattern = _ATTESTATION_EVENT_ID
    else:
        raise _error(
            "event_schema_invalid",
            "Unsupported event type.",
            "Use context_completed or usage_attested for V1 events.",
        )
    if event["schema_version"] != EVENT_SCHEMA_VERSION:
        raise _error(
            "event_schema_invalid",
            "Unsupported event schema version.",
            "Use metadata-only event schema version 1.",
        )
    event_id = _expect_string(event["event_id"], "event.event_id")
    if event_id is None or not event_id_pattern.fullmatch(event_id):
        raise _error(
            "event_schema_invalid",
            "Event ID does not match the V1 unique identifier contract.",
            "Generate the event ID through build_context_event().",
        )
    _parse_time(event["occurred_at"])
    project_id = _expect_string(event["project_id"], "event.project_id")
    if project_id is None or not _PROJECT_ID.fullmatch(project_id):
        raise _error(
            "event_schema_invalid",
            "Event project ID is not a portable project identifier.",
            "Use the validated project ID from the nearest memory manifest.",
        )

    if event_type == EVENT_TYPE_USAGE_ATTESTED:
        parent_event_id = _expect_string(
            event["parent_event_id"], "event.parent_event_id"
        )
        if parent_event_id is None or not _CONTEXT_EVENT_ID.fullmatch(parent_event_id):
            raise _error(
                "event_schema_invalid",
                "Parent event ID must identify a context_completed event.",
                "Use the event_id returned by memory context.",
            )
        payload = event["payload"]
        if not isinstance(payload, Mapping):
            raise _error(
                "event_schema_invalid",
                "Event payload must be an object.",
                "Build the event through build_usage_attestation_event().",
            )
        _validate_attestation_payload(payload)
        return

    payload = event["payload"]
    if not isinstance(payload, Mapping):
        raise _error(
            "event_schema_invalid",
            "Event payload must be an object.",
            "Build the event through build_context_event().",
        )
    _expect_exact_keys(payload, _CONTEXT_PAYLOAD_KEYS, "event.payload")
    if payload["mode"] not in _MODES:
        raise _error("event_schema_invalid", "Invalid retrieval mode.", "Use a V1 retrieval mode.")
    if payload["task_category"] not in _TASK_CATEGORIES:
        raise _error("event_schema_invalid", "Invalid task category.", "Use a V1 task category.")
    if payload["status"] not in _STATUSES:
        raise _error("event_schema_invalid", "Invalid context status.", "Use a V1 context status.")
    if payload["freshness"] not in _FRESHNESS:
        raise _error("event_schema_invalid", "Invalid freshness status.", "Use a V1 freshness status.")

    route = payload["route"]
    if not isinstance(route, list) or not route or not all(isinstance(item, str) and item for item in route):
        raise _error("event_schema_invalid", "Event route must contain collection IDs.", "Use the measured context route.")

    retrieved = payload["retrieved"]
    if not isinstance(retrieved, list):
        raise _error("event_schema_invalid", "Retrieved evidence must be a list.", "Use the measured retrieval hits.")
    for index, raw_hit in enumerate(retrieved):
        if not isinstance(raw_hit, Mapping):
            raise _error("event_schema_invalid", "Retrieved entries must be objects.", "Use normalized retrieval hits.")
        _expect_exact_keys(raw_hit, _RETRIEVED_KEYS, f"event.payload.retrieved[{index}]")
        docid = _expect_string(raw_hit["docid"], f"retrieved[{index}].docid")
        if docid is None or not _DOCID.fullmatch(docid):
            raise _error("event_schema_invalid", "Retrieved docid is invalid.", "Use the normalized QMD docid.")
        _expect_string(raw_hit["collection"], f"retrieved[{index}].collection")
        _validate_relative_path(raw_hit["path"], f"retrieved[{index}].path")
        score = raw_hit["score"]
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 1:
            raise _error("event_schema_invalid", "Retrieved score must be between 0 and 1.", "Use the normalized QMD score.")

    read = payload["read"]
    if not isinstance(read, list):
        raise _error("event_schema_invalid", "Read evidence must be a list.", "Use the emitted context sections.")
    for index, raw_section in enumerate(read):
        if not isinstance(raw_section, Mapping):
            raise _error("event_schema_invalid", "Read entries must be objects.", "Use emitted context metadata.")
        _expect_exact_keys(raw_section, _READ_KEYS, f"event.payload.read[{index}]")
        docid = _expect_string(raw_section["docid"], f"read[{index}].docid", nullable=True)
        if docid is not None and not _DOCID.fullmatch(docid):
            raise _error("event_schema_invalid", "Read docid is invalid.", "Use the emitted section docid or null.")
        _expect_string(raw_section["collection"], f"read[{index}].collection")
        _validate_relative_path(raw_section["path"], f"read[{index}].path")

    _expect_non_negative_int(payload["estimated_context_tokens"], "estimated_context_tokens")
    estimator = _expect_string(payload["estimator_version"], "estimator_version", nullable=True)
    if estimator not in {None, "utf8_bytes_div_4_v1"}:
        raise _error("event_schema_invalid", "Unknown token estimator version.", "Use the measured V1 estimator version.")
    _expect_non_negative_int(payload["budget_tokens"], "budget_tokens")
    _expect_non_negative_int(payload["duration_ms"], "duration_ms", nullable=True)
    reasons = payload["fallback_reason_codes"]
    if (
        not isinstance(reasons, list)
        or not all(isinstance(reason, str) and reason in _FALLBACK_REASONS for reason in reasons)
    ):
        raise _error("event_schema_invalid", "Fallback reasons must be a string list.", "Use measured fallback reason codes.")
    risk_reason = _expect_string(payload["risk_reason"], "risk_reason", nullable=True)
    if risk_reason not in {None, *_RISK_REASONS}:
        raise _error("event_schema_invalid", "Unknown risk reason.", "Use a V1 hard-cap risk reason.")


def build_context_event(
    metadata: Mapping[str, object],
    *,
    occurred_at: datetime | None = None,
    event_id: str | None = None,
) -> dict[str, object]:
    """Build and validate one immutable context_completed event."""

    expected_metadata = ("project_id", *_CONTEXT_PAYLOAD_KEYS)
    if len(metadata) != len(expected_metadata) or set(metadata) != set(expected_metadata):
        raise _error(
            "event_schema_invalid",
            "Context event metadata does not match the closed V1 projection.",
            "Project ContextOutcome through its event_metadata() contract.",
        )
    timestamp = _as_utc(occurred_at or _utc_now())
    event: dict[str, object] = {
        "schema_version": EVENT_SCHEMA_VERSION,
        "event_id": event_id or _new_event_id(timestamp),
        "event_type": EVENT_TYPE_CONTEXT_COMPLETED,
        "occurred_at": _format_time(timestamp),
        "project_id": metadata["project_id"],
        "payload": {key: metadata[key] for key in _CONTEXT_PAYLOAD_KEYS},
    }
    validate_event(event)
    return event


def build_usage_attestation_event(
    parent_event: Mapping[str, object],
    *,
    used: Sequence[str],
    cited: Sequence[str],
    citation_only: Sequence[str],
    impact_codes: Sequence[str],
    occurred_at: datetime | None = None,
    event_id: str | None = None,
) -> dict[str, object]:
    """Build one immutable attestation after validating it against its parent."""

    validate_event(parent_event)
    if parent_event["event_type"] != EVENT_TYPE_CONTEXT_COMPLETED:
        raise _error(
            "parent_event_invalid",
            "Usage attestations require a context_completed parent.",
            "Use the event_id returned by memory context.",
        )
    parent_payload = parent_event["payload"]
    assert isinstance(parent_payload, Mapping)
    retrieved = {
        str(hit["docid"])
        for hit in parent_payload["retrieved"]
        if isinstance(hit, Mapping)
    }
    normalized_used = _ordered_unique(used)
    normalized_cited = _ordered_unique(cited)
    normalized_citation_only = _ordered_unique(citation_only)
    normalized_impacts = _ordered_unique(impact_codes)
    unknown = sorted((set(normalized_used) | set(normalized_cited)) - retrieved)
    if unknown:
        raise _error(
            "attested_docid_not_retrieved",
            f"Attested docids were not retrieved by the parent: {', '.join(unknown)}.",
            "Attest only docids present in the parent context event.",
        )
    timestamp = _as_utc(occurred_at or _utc_now())
    event: dict[str, object] = {
        "schema_version": EVENT_SCHEMA_VERSION,
        "event_id": event_id or _new_event_id(timestamp, prefix="att"),
        "event_type": EVENT_TYPE_USAGE_ATTESTED,
        "occurred_at": _format_time(timestamp),
        "project_id": parent_event["project_id"],
        "parent_event_id": parent_event["event_id"],
        "payload": {
            "impact_taxonomy_version": IMPACT_TAXONOMY_VERSION,
            "used": normalized_used,
            "cited": normalized_cited,
            "citation_only": normalized_citation_only,
            "impact_codes": normalized_impacts,
        },
    }
    validate_event(event)
    return event


def resolve_state_dir(
    *,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    values = os.environ if environ is None else environ
    explicit = values.get("SKILLZ_MEMORY_STATE_DIR")
    if explicit:
        return Path(explicit).expanduser()
    xdg = values.get("XDG_STATE_HOME")
    if xdg:
        return Path(xdg).expanduser() / "skillz-memory"
    return (home or Path.home()) / ".local" / "state" / "skillz-memory"


def _ensure_private_directory(path: Path) -> None:
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if os.name == "posix":
        path.chmod(0o700)


def _validate_storage_location(state_dir: Path, project_root: Path | None) -> Path:
    if not state_dir.is_absolute():
        raise _error(
            "state_dir_not_absolute",
            "The memory state directory must be absolute.",
            "Set SKILLZ_MEMORY_STATE_DIR or XDG_STATE_HOME to an absolute local path.",
        )
    resolved = state_dir.resolve(strict=False)
    if project_root is not None:
        project = project_root.resolve(strict=False)
        if resolved == project or project in resolved.parents:
            raise _error(
                "state_dir_in_project",
                "The memory state directory resolves inside the current project.",
                "Choose a private state directory outside the Git worktree.",
            )
    return resolved


@contextmanager
def _project_lock(path: Path) -> Iterator[None]:
    _ensure_private_directory(path.parent)
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        if os.name == "posix":
            os.fchmod(descriptor, 0o600)
            import fcntl

            fcntl.flock(descriptor, fcntl.LOCK_EX)
        elif os.name == "nt":  # pragma: no cover - Windows adapter contract
            import msvcrt

            if os.path.getsize(path) == 0:
                os.write(descriptor, b"\0")
            os.lseek(descriptor, 0, os.SEEK_SET)
            msvcrt.locking(descriptor, msvcrt.LK_LOCK, 1)
        yield
    finally:
        if os.name == "posix":
            import fcntl

            fcntl.flock(descriptor, fcntl.LOCK_UN)
        elif os.name == "nt":  # pragma: no cover - Windows adapter contract
            import msvcrt

            os.lseek(descriptor, 0, os.SEEK_SET)
            msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
        os.close(descriptor)


def _project_directory(state_dir: Path, project_id: str) -> Path:
    events_root = state_dir / "events"
    project_dir = events_root / project_id
    if events_root.is_symlink() or project_dir.is_symlink():
        raise _error(
            "event_store_escape",
            "The project event directory cannot be a symbolic link.",
            "Restore a private physical event directory beneath the state root.",
        )
    resolved_events = events_root.resolve(strict=False)
    resolved_project = project_dir.resolve(strict=False)
    if resolved_events not in resolved_project.parents:
        raise _error(
            "event_store_escape",
            "The project event directory escapes the private event root.",
            "Restore the private event directory and retry.",
        )
    return project_dir


def _event_path(project_dir: Path, event: Mapping[str, object]) -> Path:
    occurred_at = _parse_time(event["occurred_at"])
    return project_dir / f"{occurred_at:%Y-%m}.jsonl"


def _append_event_line(event_path: Path, event: Mapping[str, object]) -> None:
    encoded = (
        json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    _ensure_private_directory(event_path.parent)
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(event_path, flags, 0o600)
    try:
        if os.name == "posix":
            os.fchmod(descriptor, 0o600)
        view = memoryview(encoded)
        while view:
            written = os.write(descriptor, view)
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def append_event(
    event: Mapping[str, object],
    *,
    state_dir: Path | None = None,
    project_root: Path | None = None,
) -> Path:
    """Validate before mutation, then append one compact and fsynced JSON line."""

    validate_event(event)
    root = _validate_storage_location(state_dir or resolve_state_dir(), project_root)
    project_dir = _project_directory(root, str(event["project_id"]))
    event_path = _event_path(project_dir, event)
    lock_path = root / "events" / f".{event['project_id']}.lock"

    try:
        _ensure_private_directory(root)
        with _project_lock(lock_path):
            _append_event_line(event_path, event)
    except OSError as error:
        raise _error(
            "event_store_unavailable",
            "The metadata-only event could not be persisted safely.",
            "Restore access to the private memory state directory, then retry.",
        ) from error
    return event_path


def append_usage_attestation(
    *,
    project_id: str,
    parent_event_id: str,
    used: Sequence[str],
    cited: Sequence[str],
    citation_only: Sequence[str],
    impact_codes: Sequence[str],
    state_dir: Path | None = None,
    project_root: Path | None = None,
    occurred_at: datetime | None = None,
) -> UsageAttestationResult:
    """Lookup, validate and append one attestation under one project lock."""

    if not _PROJECT_ID.fullmatch(project_id):
        raise _error(
            "event_schema_invalid",
            "Attestation project ID is invalid.",
            "Use the project ID from the nearest validated memory manifest.",
        )
    if not _CONTEXT_EVENT_ID.fullmatch(parent_event_id):
        raise _error(
            "parent_event_invalid",
            "Parent event ID must identify a context_completed event.",
            "Use the event_id returned by memory context.",
        )
    root = _validate_storage_location(state_dir or resolve_state_dir(), project_root)
    project_dir = _project_directory(root, project_id)
    lock_path = root / "events" / f".{project_id}.lock"
    try:
        _ensure_private_directory(root)
        with _project_lock(lock_path):
            parents: list[dict[str, Any]] = []
            already_attested = False
            diagnostics: list[dict[str, str]] = []
            if project_dir.exists():
                for path in sorted(project_dir.glob("*.jsonl")):
                    result = read_event_file(path)
                    diagnostics.extend(result.diagnostics)
                    for stored_event in result.events:
                        if stored_event["event_id"] == parent_event_id:
                            parents.append(stored_event)
                        if (
                            stored_event["event_type"] == EVENT_TYPE_USAGE_ATTESTED
                            and stored_event["parent_event_id"] == parent_event_id
                        ):
                            already_attested = True
            if diagnostics:
                raise _error(
                    "event_log_truncated",
                    "The project event log has an incomplete final line.",
                    "Run memory purge before appending an attestation.",
                )
            if not parents:
                raise _error(
                    "parent_event_not_found",
                    f"Parent context event was not found: {parent_event_id}.",
                    "Use a retained event_id from memory context in the current project.",
                )
            if len(parents) != 1:
                raise _error(
                    "parent_event_ambiguous",
                    f"Parent context event is duplicated: {parent_event_id}.",
                    "Inspect or purge the affected local project telemetry.",
                )
            if already_attested:
                raise _error(
                    "parent_already_attested",
                    f"Parent context event is already attested: {parent_event_id}.",
                    "Reuse the existing immutable attestation instead of appending another.",
                )
            event = build_usage_attestation_event(
                parents[0],
                used=used,
                cited=cited,
                citation_only=citation_only,
                impact_codes=impact_codes,
                occurred_at=occurred_at,
            )
            _append_event_line(_event_path(project_dir, event), event)
    except OSError as error:
        raise _error(
            "event_store_unavailable",
            "The usage attestation could not be persisted safely.",
            "Restore access to the private memory state directory, then retry.",
        ) from error
    return UsageAttestationResult(parents[0], event)


def read_event_file(path: Path) -> EventReadResult:
    """Read valid JSONL prefix and diagnose only an incomplete final line."""

    if path.is_symlink():
        raise _error(
            "event_store_escape",
            "An event log cannot be a symbolic link.",
            "Restore a private physical JSONL file beneath the project event directory.",
        )
    try:
        serialized = path.read_text(encoding="utf-8")
        lines = serialized.splitlines()
    except (OSError, UnicodeError) as error:
        raise _error(
            "event_log_unreadable",
            "The local event log cannot be read safely.",
            "Restore local file access or purge the affected project telemetry.",
        ) from error

    events: list[dict[str, Any]] = []
    diagnostics: list[dict[str, str]] = []
    for index, line in enumerate(lines):
        try:
            raw = json.loads(
                line,
                object_pairs_hook=_strict_json_object,
                parse_constant=_reject_json_constant,
            )
        except json.JSONDecodeError as error:
            if index == len(lines) - 1 and not serialized.endswith("\n"):
                diagnostics.append(
                    {
                        "code": "truncated_event_tail",
                        "message": "The final event line is incomplete or invalid and was ignored.",
                        "correction": "Run memory purge to rewrite the valid prefix safely.",
                    }
                )
                break
            raise _error(
                "event_log_corrupt",
                "A non-final event line is invalid; the log prefix is not trustworthy.",
                "Inspect or purge the affected local project telemetry.",
            ) from error
        except ValueError as error:
            raise _error(
                "event_log_corrupt",
                "An event line is not strict JSON.",
                "Inspect or purge the affected local project telemetry.",
            ) from error
        if not isinstance(raw, dict):
            raise _error(
                "event_log_corrupt",
                "An event line is not a JSON object.",
                "Inspect or purge the affected local project telemetry.",
            )
        try:
            validate_event(raw)
        except EventIntegrityError as error:
            raise _error(
                "event_log_corrupt",
                "An event line violates the metadata-only V1 contract.",
                "Inspect or purge the affected local project telemetry.",
            ) from error
        events.append(raw)
    return EventReadResult(tuple(events), tuple(diagnostics))


def _write_events_atomically(path: Path, events: Sequence[Mapping[str, object]]) -> None:
    _ensure_private_directory(path.parent)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        if os.name == "posix":
            os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            for event in events:
                stream.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")))
                stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def purge_project_events(
    project_id: str,
    *,
    retention_days: int,
    force: bool = False,
    state_dir: Path | None = None,
    project_root: Path | None = None,
    now: datetime | None = None,
) -> PurgeOutcome:
    """Apply retention, or remove all detail, for exactly one validated project."""

    if not _PROJECT_ID.fullmatch(project_id):
        raise _error(
            "event_schema_invalid",
            "Purge project ID is invalid.",
            "Use the project ID from the nearest validated memory manifest.",
        )
    if isinstance(retention_days, bool) or not isinstance(retention_days, int) or retention_days <= 0:
        raise _error(
            "event_schema_invalid",
            "Retention must be a positive number of days.",
            "Use policy.retention_days from the validated memory manifest.",
        )
    root = _validate_storage_location(state_dir or resolve_state_dir(), project_root)
    project_dir = _project_directory(root, project_id)
    if not project_dir.exists():
        return PurgeOutcome(project_id, retention_days, force, 0, 0, 0, 0)

    lock_path = root / "events" / f".{project_id}.lock"
    cutoff = _as_utc(now or _utc_now()) - timedelta(days=retention_days)
    deleted_events = retained_events = removed_files = corrupted_files = 0
    try:
        with _project_lock(lock_path):
            for path in sorted(project_dir.glob("*.jsonl")):
                result = read_event_file(path)
                corrupted_files += int(bool(result.diagnostics))
                retained: list[dict[str, Any]] = []
                for event in result.events:
                    if force or _parse_time(event["occurred_at"]) < cutoff:
                        deleted_events += 1
                    else:
                        retained.append(event)
                        retained_events += 1
                if retained:
                    if len(retained) != len(result.events) or result.diagnostics:
                        _write_events_atomically(path, retained)
                else:
                    path.unlink(missing_ok=True)
                    removed_files += 1
            if project_dir.exists() and not any(project_dir.iterdir()):
                project_dir.rmdir()
    except OSError as error:
        raise _error(
            "event_store_unavailable",
            "The project event store could not be purged safely.",
            "Restore access to the private memory state directory, then retry.",
        ) from error
    return PurgeOutcome(
        project_id=project_id,
        retention_days=retention_days,
        force=force,
        deleted_events=deleted_events,
        retained_events=retained_events,
        removed_files=removed_files,
        corrupted_files=corrupted_files,
    )
