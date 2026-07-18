"""Bounded adapter for the human-readable QMD 0.9.x status contract."""

from __future__ import annotations

import re
import subprocess
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass


SUPPORTED_MAJOR = 0
SUPPORTED_MINOR = 9
MAX_OUTPUT_BYTES = 1024 * 1024
VERSION_PATTERN = re.compile(r"\bqmd\s+(\d+)\.(\d+)\.(\d+)\b", re.IGNORECASE)
COLLECTION_PATTERN = re.compile(
    r"^\s{2}(?P<name>[a-z0-9][a-z0-9-]{1,62})\s+\(qmd://(?P=name)/\)\s*$"
)
FILES_PATTERN = re.compile(
    r"^\s{4}Files:\s+(?P<files>\d+)\s+\(updated\s+(?P<age>[^)]+)\)\s*$"
)
AGE_PATTERN = re.compile(r"^(?P<value>\d+)(?P<unit>[smhdw])\s+ago$")


class QmdOutputError(Exception):
    """QMD output did not match the supported, fixture-backed 0.9.x contract."""


class QmdInvocationError(Exception):
    """QMD could not be executed safely or returned a non-zero status."""


@dataclass(frozen=True, slots=True)
class QmdCollectionStatus:
    name: str
    files: int
    age_seconds: int


@dataclass(frozen=True, slots=True)
class QmdStatus:
    version: tuple[int, int, int]
    collections: Mapping[str, QmdCollectionStatus]


Runner = Callable[..., subprocess.CompletedProcess[str]]


def parse_qmd_version(output: str) -> tuple[int, int, int]:
    match = VERSION_PATTERN.search(output.strip())
    if match is None:
        raise QmdOutputError("QMD version output is not recognized.")
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def _age_seconds(raw_age: str) -> int:
    normalized = raw_age.strip().lower()
    if normalized in {"just now", "now"}:
        return 0
    match = AGE_PATTERN.fullmatch(normalized)
    if match is None:
        raise QmdOutputError("QMD collection age is not recognized.")
    multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
    return int(match.group("value")) * multipliers[match.group("unit")]


def parse_qmd_status(output: str) -> dict[str, QmdCollectionStatus]:
    collections: dict[str, QmdCollectionStatus] = {}
    pending_name: str | None = None
    for line in output.splitlines():
        collection_match = COLLECTION_PATTERN.match(line)
        if collection_match is not None:
            pending_name = collection_match.group("name")
            continue
        if pending_name is None:
            continue
        files_match = FILES_PATTERN.match(line)
        if files_match is None:
            continue
        collections[pending_name] = QmdCollectionStatus(
            name=pending_name,
            files=int(files_match.group("files")),
            age_seconds=_age_seconds(files_match.group("age")),
        )
        pending_name = None
    if not collections:
        raise QmdOutputError("QMD status contains no parseable collections.")
    return collections


def _run_qmd(
    executable: str,
    arguments: Sequence[str],
    *,
    runner: Runner,
    timeout_seconds: float,
) -> str:
    try:
        result = runner(
            [executable, *arguments],
            check=False,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise QmdInvocationError("QMD invocation failed or timed out.") from error
    if result.returncode != 0:
        raise QmdInvocationError("QMD returned a non-zero status.")
    if len(result.stdout.encode("utf-8")) > MAX_OUTPUT_BYTES:
        raise QmdOutputError("QMD output exceeds the supported size limit.")
    return result.stdout


def inspect_qmd(
    executable: str,
    *,
    runner: Runner = subprocess.run,
    timeout_seconds: float = 1.0,
) -> QmdStatus:
    version = parse_qmd_version(
        _run_qmd(executable, ["--version"], runner=runner, timeout_seconds=timeout_seconds)
    )
    if version[0] != SUPPORTED_MAJOR or version[1] != SUPPORTED_MINOR:
        raise QmdOutputError("Only QMD >=0.9,<0.10 is supported by this adapter.")
    collections = parse_qmd_status(
        _run_qmd(executable, ["status"], runner=runner, timeout_seconds=timeout_seconds)
    )
    return QmdStatus(version=version, collections=collections)
