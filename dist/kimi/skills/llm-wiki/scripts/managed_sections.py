#!/usr/bin/env python3
"""Hash-attested managed Markdown sections for safe regeneration."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re


MARKER_NAMESPACE = "skillz-llm-wiki:managed"
MARKER_VERSION = 1


class ManagedSectionError(RuntimeError):
    """Raised when an existing managed section cannot be trusted."""


@dataclass(frozen=True)
class ManagedSection:
    prefix: str
    body: str
    suffix: str
    digest: str


def _normalize_body(body: str) -> str:
    return body if body.endswith("\n") else body + "\n"


def _digest(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _start_marker(section: str, digest: str) -> str:
    return (
        f"<!-- {MARKER_NAMESPACE}:{section}:v{MARKER_VERSION} "
        f"sha256={digest} -->"
    )


def _end_marker(section: str) -> str:
    return f"<!-- /{MARKER_NAMESPACE}:{section} -->"


def render_managed_section(section: str, body: str) -> str:
    """Wrap normalized content in exact, hash-attested ownership markers."""

    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", section):
        raise ValueError(f"invalid managed section name: {section}")
    normalized = _normalize_body(body)
    return (
        f"{_start_marker(section, _digest(normalized))}\n"
        f"{normalized}"
        f"{_end_marker(section)}\n"
    )


def parse_managed_section(document: str, section: str) -> ManagedSection:
    """Validate exact markers and the content hash before any replacement."""

    start_pattern = re.compile(
        rf"(?m)^<!-- {re.escape(MARKER_NAMESPACE)}:{re.escape(section)}:"
        rf"v{MARKER_VERSION} sha256=([0-9a-f]{{64}}) -->\n"
    )
    end_pattern = re.compile(
        rf"(?m)^<!-- /{re.escape(MARKER_NAMESPACE)}:{re.escape(section)} -->\n?"
    )
    starts = list(start_pattern.finditer(document))
    ends = list(end_pattern.finditer(document))
    if len(starts) != 1 or len(ends) != 1:
        raise ManagedSectionError(
            f"managed section {section!r} requires exactly one intact marker pair"
        )
    start, end = starts[0], ends[0]
    if start.end() > end.start():
        raise ManagedSectionError(f"managed section {section!r} markers are out of order")
    body = document[start.end() : end.start()]
    expected = start.group(1)
    actual = _digest(body)
    if actual != expected:
        raise ManagedSectionError(
            f"managed section {section!r} content drifted "
            f"(expected sha256={expected}, actual sha256={actual})"
        )
    return ManagedSection(
        prefix=document[: start.start()],
        body=body,
        suffix=document[end.end() :],
        digest=expected,
    )


def prepare_managed_update(
    existing: str | None,
    section: str,
    body: str,
) -> tuple[str, bool]:
    """Return the safe next document and whether bytes need to be written."""

    rendered = render_managed_section(section, body)
    if existing is None:
        return rendered, True
    current = parse_managed_section(existing, section)
    candidate = current.prefix + rendered + current.suffix
    return candidate, candidate != existing
