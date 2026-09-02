"""Bounded adapter for QMD 0.9.x status and lexical-search contracts."""

from __future__ import annotations

import json
import math
import re
import subprocess
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import PurePosixPath
from typing import Any, NoReturn

from .contracts import RetrievalHit


SUPPORTED_MAJOR = 0
SUPPORTED_MINOR = 9
MAX_OUTPUT_BYTES = 1024 * 1024
MAX_TIMEOUT_SECONDS = 30.0
DEFAULT_SEARCH_TIMEOUT_SECONDS = 8.0
VERSION_PATTERN = re.compile(r"\bqmd\s+(\d+)\.(\d+)\.(\d+)\b", re.IGNORECASE)
COLLECTION_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")
COLLECTION_PATTERN = re.compile(
    r"^\s{2}(?P<name>[a-z0-9][a-z0-9-]{1,62})\s+\(qmd://(?P=name)/\)\s*$"
)
FILES_PATTERN = re.compile(
    r"^\s{4}Files:\s+(?P<files>\d+)\s+\(updated\s+(?P<age>[^)]+)\)\s*$"
)
AGE_PATTERN = re.compile(r"^(?P<value>\d+)(?P<unit>[smhdw])\s+ago$")
DOCID_PATTERN = re.compile(r"^#[0-9a-f]{6,64}$")
SNIPPET_LINE_PATTERN = re.compile(
    r"^@@\s+-(?P<line>\d+)(?:,\d+)?\s+@@(?:\s+\([^)]+\))?"
)


class QmdOutputError(Exception):
    """QMD output did not match the supported, fixture-backed 0.9.x contract."""


class QmdInvocationError(Exception):
    """QMD could not be executed safely or returned a non-zero status."""


class QmdTimeoutError(QmdInvocationError):
    """QMD exceeded the bounded route timeout."""


class QmdSearchStatus(str, Enum):
    READY = "ready"
    EMPTY = "empty"
    TIMEOUT = "timeout"
    INVALID = "invalid"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class QmdCollectionStatus:
    name: str
    files: int
    age_seconds: int


@dataclass(frozen=True, slots=True)
class QmdStatus:
    version: tuple[int, int, int]
    collections: Mapping[str, QmdCollectionStatus]


@dataclass(frozen=True, slots=True)
class QmdSearchOutcome:
    status: QmdSearchStatus
    hits: tuple[RetrievalHit, ...]
    duration_ms: int


Runner = Callable[..., subprocess.CompletedProcess[str]]
Timer = Callable[[], float]


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate QMD JSON key")
        result[key] = value
    return result


def _reject_json_constant(_: str) -> NoReturn:
    raise ValueError("non-standard QMD JSON constant")


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
    if timeout_seconds <= 0 or timeout_seconds > MAX_TIMEOUT_SECONDS:
        raise ValueError(
            f"QMD timeout must be greater than zero and at most {MAX_TIMEOUT_SECONDS:g} seconds."
        )
    try:
        result = runner(
            [executable, *arguments],
            check=False,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            shell=False,
        )
    except subprocess.TimeoutExpired as error:
        raise QmdTimeoutError("QMD invocation timed out.") from error
    except OSError as error:
        raise QmdInvocationError("QMD invocation failed.") from error
    if not isinstance(result.stdout, str) or not isinstance(result.stderr, str):
        raise QmdOutputError("QMD did not return text output.")
    if (
        len(result.stdout.encode("utf-8")) > MAX_OUTPUT_BYTES
        or len(result.stderr.encode("utf-8")) > MAX_OUTPUT_BYTES
    ):
        raise QmdOutputError("QMD output exceeds the supported size limit.")
    if result.returncode != 0:
        raise QmdInvocationError("QMD returned a non-zero status.")
    return result.stdout


def parse_qmd_search(
    output: str,
    *,
    expected_collection: str,
) -> tuple[RetrievalHit, ...]:
    """Normalize the fixture-backed JSON emitted by ``qmd search --json``."""

    if COLLECTION_NAME_PATTERN.fullmatch(expected_collection) is None:
        raise QmdOutputError("The expected QMD collection name is invalid.")
    try:
        payload = json.loads(
            output,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_json_constant,
        )
    except (json.JSONDecodeError, ValueError) as error:
        raise QmdOutputError("QMD search output is not valid strict JSON.") from error
    if not isinstance(payload, list):
        raise QmdOutputError("QMD search output must be a JSON array.")

    hits: list[RetrievalHit] = []
    prefix = f"qmd://{expected_collection}/"
    required_fields = {"docid", "score", "file", "title", "snippet"}
    for index, item in enumerate(payload):
        if not isinstance(item, dict) or not required_fields.issubset(item):
            raise QmdOutputError(f"QMD search result {index} is missing required fields.")
        docid = item["docid"]
        score = item["score"]
        file_uri = item["file"]
        title = item["title"]
        raw_snippet = item["snippet"]
        if not isinstance(docid, str) or DOCID_PATTERN.fullmatch(docid) is None:
            raise QmdOutputError(f"QMD search result {index} has an invalid docid.")
        if (
            isinstance(score, bool)
            or not isinstance(score, (int, float))
            or not math.isfinite(float(score))
        ):
            raise QmdOutputError(f"QMD search result {index} has an invalid score.")
        if not isinstance(file_uri, str) or not file_uri.startswith(prefix):
            raise QmdOutputError(
                f"QMD search result {index} is outside the requested collection."
            )
        relative_raw = file_uri[len(prefix) :]
        relative_path = PurePosixPath(relative_raw)
        if (
            not relative_raw
            or relative_path.is_absolute()
            or "\\" in relative_raw
            or relative_path.as_posix() != relative_raw
            or any(part in {"", ".", ".."} for part in relative_path.parts)
        ):
            raise QmdOutputError(f"QMD search result {index} has an unsafe path.")
        if not isinstance(title, str) or not title.strip():
            raise QmdOutputError(f"QMD search result {index} has an invalid title.")
        if not isinstance(raw_snippet, str):
            raise QmdOutputError(f"QMD search result {index} has an invalid snippet.")
        snippet_match = SNIPPET_LINE_PATTERN.match(raw_snippet)
        if snippet_match is None:
            raise QmdOutputError(
                f"QMD search result {index} has no recognized snippet line."
            )
        if not 0 <= float(score) <= 1 or int(snippet_match.group("line")) < 1:
            raise QmdOutputError(
                f"QMD search result {index} has out-of-range normalized values."
            )
        snippet = raw_snippet[snippet_match.end() :].lstrip("\r\n")
        hits.append(
            RetrievalHit(
                docid=docid,
                collection=expected_collection,
                relative_path=relative_path,
                title=title,
                score=float(score),
                snippet_line=int(snippet_match.group("line")),
                snippet=snippet,
            )
        )
    return tuple(hits)


def search_qmd(
    executable: str,
    *,
    query: str,
    collection: str,
    limit: int,
    min_score: float,
    runner: Runner = subprocess.run,
    timeout_seconds: float = DEFAULT_SEARCH_TIMEOUT_SECONDS,
    timer: Timer = time.monotonic,
) -> QmdSearchOutcome:
    """Run one bounded lexical project search without persisting the query."""

    if not executable:
        raise ValueError("QMD executable must not be empty.")
    if not query.strip():
        raise ValueError("QMD query must not be empty.")
    if COLLECTION_NAME_PATTERN.fullmatch(collection) is None:
        raise ValueError("QMD collection name is invalid.")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("QMD result limit must be between 1 and 100.")
    if (
        isinstance(min_score, bool)
        or not isinstance(min_score, (int, float))
        or not math.isfinite(float(min_score))
        or not 0 <= float(min_score) <= 1
    ):
        raise ValueError("QMD minimum score must be between zero and one.")

    started_at = timer()
    output = _run_qmd(
        executable,
        [
            "search",
            query,
            "--json",
            "-c",
            collection,
            "-n",
            str(limit),
            "--min-score",
            format(float(min_score), "g"),
        ],
        runner=runner,
        timeout_seconds=timeout_seconds,
    )
    hits = parse_qmd_search(output, expected_collection=collection)
    duration_ms = max(0, round((timer() - started_at) * 1000))
    return QmdSearchOutcome(
        status=QmdSearchStatus.READY if hits else QmdSearchStatus.EMPTY,
        hits=hits,
        duration_ms=duration_ms,
    )


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
