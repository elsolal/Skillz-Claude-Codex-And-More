"""Deterministic golden retrieval comparison and metadata-only run storage."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import secrets
import tempfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from statistics import median
from typing import Any

from .assembly import DocumentAccessError, resolve_document
from .context import run_context
from .contracts import MemoryManifest, RetrievalHit, RetrievalMode, TaskCategory
from .events import (
    EventIntegrityError,
    ensure_private_state_directory,
    fsync_state_directory,
    scan_metadata_privacy,
    validate_state_directory,
)
from .manifest import load_manifest
from .projection import load_projection
from .receipts import ContextOutcome, GoldenTestOutcome
from .tokens import ESTIMATOR_VERSION, estimate_tokens


GOLDEN_SCHEMA_VERSION = 1
GOLDEN_RUN_SCHEMA_VERSION = 1
GOLDEN_VISIBLE_CASES = 8
BASELINE_MIN_PAGES = 3
BASELINE_MAX_PAGES = 10
MAX_GOLDEN_QUERY_CHARACTERS = 16 * 1024

_CASE_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
_RUN_ID = re.compile(r"^run_\d{8}T\d{12}Z_[0-9a-f]{16}$")


class GoldenContractError(RuntimeError):
    """Stable golden schema, execution or persistence failure."""

    def __init__(
        self,
        *,
        code: str,
        message: str,
        correction: str,
        exit_code: int = 30,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.correction = correction
        self.exit_code = exit_code

    def as_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "message": self.message,
            "correction": self.correction,
        }


def _error(
    code: str,
    message: str,
    correction: str,
    *,
    exit_code: int = 30,
) -> GoldenContractError:
    return GoldenContractError(
        code=code,
        message=message,
        correction=correction,
        exit_code=exit_code,
    )


@dataclass(frozen=True, slots=True)
class GoldenCase:
    case_id: str
    query: str
    task_category: TaskCategory
    expected_pages: tuple[PurePosixPath, ...]
    expected_sources: tuple[PurePosixPath, ...]
    baseline_pages: tuple[PurePosixPath, ...]

    @property
    def expectations(self) -> tuple[tuple[str, PurePosixPath], ...]:
        return tuple(("page", path) for path in self.expected_pages) + tuple(
            ("source", path) for path in self.expected_sources
        )


@dataclass(frozen=True, slots=True)
class GoldenSuite:
    schema_version: int
    cases: tuple[GoldenCase, ...]


@dataclass(frozen=True, slots=True)
class RouteMeasurement:
    status: str
    docids: tuple[str, ...]
    ranks: Mapping[PurePosixPath, tuple[int, str]]
    estimated_tokens: int
    fallback_used: bool


def _strict_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate golden key: {key}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")


def _object(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise _error(
            "golden_case_schema_invalid",
            f"{field} must be a JSON object.",
            "Use the closed golden V1 object schema.",
        )
    return value


def _exact_keys(
    value: Mapping[str, Any],
    field: str,
    *,
    required: set[str],
) -> None:
    actual = set(value)
    if actual != required:
        missing = sorted(required - actual)
        unknown = sorted(actual - required)
        details = []
        if missing:
            details.append(f"missing: {', '.join(missing)}")
        if unknown:
            details.append(f"unknown: {', '.join(unknown)}")
        raise _error(
            "golden_case_schema_invalid",
            f"{field} does not match golden V1 ({'; '.join(details)}).",
            "Add every required field and remove unknown fields.",
        )


def _safe_path(
    value: object,
    field: str,
    *,
    source: bool = False,
    page: bool = False,
) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        raise _error(
            "golden_path_invalid",
            f"{field} must be a non-empty relative POSIX path.",
            "Use a versioned path beneath wiki/.",
        )
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or "\\" in value
        or any(part in {"", ".", ".."} for part in path.parts)
        or path.parts[:1] != ("wiki",)
        or path.suffix.lower() != ".md"
    ):
        raise _error(
            "golden_path_invalid",
            f"{field} must stay beneath wiki/ and name one Markdown page.",
            "Remove absolute paths, traversal and non-Markdown targets.",
        )
    if source and path.parts[:2] != ("wiki", "sources"):
        raise _error(
            "golden_path_invalid",
            f"{field} must identify a page beneath wiki/sources/.",
            "Classify source expectations separately from other wiki pages.",
        )
    if page and (
        path.parts[:2] == ("wiki", "sources")
        or path == PurePosixPath("wiki/index.md")
    ):
        raise _error(
            "golden_path_invalid",
            f"{field} must identify a non-source wiki page.",
            "Classify source evidence separately and keep wiki/index.md out of expectations.",
        )
    return path


def _path_list(
    value: object,
    field: str,
    *,
    source: bool = False,
    page: bool = False,
    allow_empty: bool = True,
) -> tuple[PurePosixPath, ...]:
    if not isinstance(value, list):
        raise _error(
            "golden_case_schema_invalid",
            f"{field} must be a path list.",
            "Use a JSON array of relative wiki Markdown paths.",
        )
    paths = tuple(
        _safe_path(item, f"{field}[{index}]", source=source, page=page)
        for index, item in enumerate(value)
    )
    if not allow_empty and not paths:
        raise _error(
            "golden_case_schema_invalid",
            f"{field} must not be empty.",
            "Declare the deterministic index-first drill-in pages.",
        )
    if len(paths) != len(set(paths)):
        raise _error(
            "golden_case_schema_invalid",
            f"{field} contains duplicate paths.",
            "Keep each expected page once, in stable order.",
        )
    return paths


def _parse_case(raw: object, index: int) -> GoldenCase:
    field = f"cases[{index}]"
    data = _object(raw, field)
    _exact_keys(
        data,
        field,
        required={"id", "query", "task_category", "expected", "baseline"},
    )
    case_id = data["id"]
    if not isinstance(case_id, str) or _CASE_ID.fullmatch(case_id) is None:
        raise _error(
            "golden_case_schema_invalid",
            f"{field}.id must be a lowercase stable slug.",
            "Use 1-63 lowercase letters, digits and hyphens.",
        )
    query = data["query"]
    if (
        not isinstance(query, str)
        or not query
        or query != query.strip()
        or "\n" in query
        or "\r" in query
        or len(query) > MAX_GOLDEN_QUERY_CHARACTERS
    ):
        raise _error(
            "golden_case_schema_invalid",
            f"{field}.query must be one sanitized non-empty line.",
            "Human-review and trim the query before versioning the golden case.",
        )
    try:
        task_category = TaskCategory(data["task_category"])
    except (TypeError, ValueError) as error:
        raise _error(
            "golden_case_schema_invalid",
            f"{field}.task_category is not a task-category V1 value.",
            "Use one of the categories accepted by memory context.",
        ) from error
    try:
        scan_metadata_privacy(query, field=f"{field}.query")
    except EventIntegrityError as error:
        raise _error(
            "golden_query_privacy_invalid",
            f"{field}.query contains private or secret-shaped material.",
            "Replace it with a human-sanitized visible golden question.",
        ) from error

    expected = _object(data["expected"], f"{field}.expected")
    _exact_keys(expected, f"{field}.expected", required={"pages", "sources"})
    expected_pages = _path_list(
        expected["pages"],
        f"{field}.expected.pages",
        page=True,
    )
    expected_sources = _path_list(
        expected["sources"],
        f"{field}.expected.sources",
        source=True,
    )
    if not expected_pages and not expected_sources:
        raise _error(
            "golden_expectations_empty",
            f"{field} declares no page or source expectation.",
            "Declare at least one human-validated expected artifact.",
        )
    if set(expected_pages) & set(expected_sources):
        raise _error(
            "golden_case_schema_invalid",
            f"{field} classifies the same path as both page and source.",
            "Classify each expected artifact once.",
        )

    baseline = _object(data["baseline"], f"{field}.baseline")
    _exact_keys(baseline, f"{field}.baseline", required={"pages"})
    baseline_pages = _path_list(
        baseline["pages"],
        f"{field}.baseline.pages",
        allow_empty=False,
    )
    if not BASELINE_MIN_PAGES <= len(baseline_pages) <= BASELINE_MAX_PAGES:
        raise _error(
            "golden_case_schema_invalid",
            f"{field}.baseline.pages must contain 3-10 deterministic drill-in pages.",
            "Replay the approved historical index-first envelope.",
        )
    if PurePosixPath("wiki/index.md") in baseline_pages:
        raise _error(
            "golden_case_schema_invalid",
            f"{field}.baseline.pages must not repeat wiki/index.md.",
            "The index-first adapter already loads the complete index once.",
        )
    missing = (set(expected_pages) | set(expected_sources)) - set(baseline_pages)
    if missing:
        raise _error(
            "golden_baseline_incomplete",
            f"{field}.baseline.pages omits expected evidence.",
            "Include every expected page/source in the explicit baseline replay.",
        )
    return GoldenCase(
        case_id=case_id,
        query=query,
        task_category=task_category,
        expected_pages=expected_pages,
        expected_sources=expected_sources,
        baseline_pages=baseline_pages,
    )


def load_golden_suite(path: Path) -> GoldenSuite:
    """Load and fully validate the visible golden set before any retrieval."""

    if path.is_symlink():
        raise _error(
            "golden_file_escape",
            "The visible golden file cannot be a symbolic link.",
            "Restore the versioned physical golden file beneath the project root.",
        )
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_strict_json_object,
            parse_constant=_reject_json_constant,
        )
    except FileNotFoundError as error:
        raise _error(
            "golden_file_missing",
            "The manifest-declared visible golden file is missing.",
            "Add the approved golden V1 file or correct golden.visible_path.",
        ) from error
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise _error(
            "golden_file_invalid",
            "The visible golden file is not strict readable JSON.",
            "Repair the JSON document before running memory test.",
        ) from error
    data = _object(payload, "golden")
    _exact_keys(data, "golden", required={"schema_version", "cases"})
    if data["schema_version"] != GOLDEN_SCHEMA_VERSION:
        raise _error(
            "golden_schema_unknown",
            "The visible golden file uses an unknown schema version.",
            f"Use golden schema version {GOLDEN_SCHEMA_VERSION}.",
        )
    raw_cases = data["cases"]
    if not isinstance(raw_cases, list) or len(raw_cases) != GOLDEN_VISIBLE_CASES:
        raise _error(
            "golden_case_count_invalid",
            f"Golden V1 requires exactly {GOLDEN_VISIBLE_CASES} visible cases.",
            "Keep holdouts separate and provide all eight visible cases.",
        )
    cases = tuple(_parse_case(raw, index) for index, raw in enumerate(raw_cases))
    case_ids = [case.case_id for case in cases]
    if len(case_ids) != len(set(case_ids)):
        raise _error(
            "golden_case_id_duplicate",
            "Golden case IDs must be unique.",
            "Assign a stable unique slug to every visible case.",
        )
    return GoldenSuite(schema_version=GOLDEN_SCHEMA_VERSION, cases=cases)


def _canonical_wiki_path(path: PurePosixPath) -> PurePosixPath:
    if path.parts[:1] == ("wiki",):
        return path
    return PurePosixPath("wiki", *path.parts)


def _collection_relative(path: PurePosixPath) -> PurePosixPath:
    if path.parts[:1] == ("wiki",):
        return PurePosixPath(*path.parts[1:])
    return path


def _stable_docid(collection: str, path: PurePosixPath) -> str:
    digest = hashlib.sha256(f"{collection}:{path.as_posix()}".encode("utf-8")).hexdigest()
    return f"#{digest[:12]}"


def _ordered_docids(hits: Sequence[RetrievalHit]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(hit.docid for hit in hits))


def _rank_hits(hits: Sequence[RetrievalHit]) -> dict[PurePosixPath, tuple[int, str]]:
    ranks: dict[PurePosixPath, tuple[int, str]] = {}
    for rank, hit in enumerate(hits, start=1):
        path = _canonical_wiki_path(hit.relative_path)
        ranks.setdefault(path, (rank, hit.docid))
    return ranks


def _measure_baseline(
    case: GoldenCase,
    *,
    query: str,
    collection: str,
    root: Path,
) -> RouteMeasurement:
    """Replay index-first with explicit 3-10 pages; query stays memory-only."""

    if query != case.query:
        raise AssertionError("paired baseline query diverged from the golden case")
    try:
        index_path = resolve_document(root, PurePosixPath("index.md"))
        texts = [index_path.read_text(encoding="utf-8")]
        ranks: dict[PurePosixPath, tuple[int, str]] = {}
        docids: list[str] = []
        for rank, relative_path in enumerate(case.baseline_pages, start=1):
            path = resolve_document(root, _collection_relative(relative_path))
            texts.append(path.read_text(encoding="utf-8"))
            docid = _stable_docid(collection, relative_path)
            docids.append(docid)
            ranks[relative_path] = (rank, docid)
    except (DocumentAccessError, OSError, UnicodeError) as error:
        raise _error(
            "golden_baseline_unavailable",
            f"The explicit index-first baseline for case {case.case_id!r} is unavailable.",
            "Restore wiki/index.md and every declared baseline page before comparison.",
        ) from error
    estimated_tokens = sum(estimate_tokens(text) for text in texts)
    if estimated_tokens <= 0:
        raise _error(
            "golden_baseline_empty",
            f"The explicit index-first baseline for case {case.case_id!r} is empty.",
            "Restore non-empty index and baseline evidence before comparison.",
        )
    return RouteMeasurement(
        status="ready",
        docids=tuple(docids),
        ranks=ranks,
        estimated_tokens=estimated_tokens,
        fallback_used=False,
    )


def _measure_bounded(
    case: GoldenCase,
    *,
    query: str,
    project_collection: str,
    runner: Callable[..., ContextOutcome],
) -> RouteMeasurement:
    if query != case.query:
        raise AssertionError("paired bounded query diverged from the golden case")
    outcome = runner(
        mode=RetrievalMode.PROJECT,
        task_category=case.task_category,
        query=query,
        fallback_on_ambiguous=True,
    )
    first_route_hits = tuple(
        hit for hit in outcome.hits if hit.collection == project_collection
    )
    return RouteMeasurement(
        status=outcome.status,
        docids=_ordered_docids(outcome.hits),
        ranks=_rank_hits(first_route_hits),
        estimated_tokens=(
            outcome.assembly.estimated_tokens if outcome.assembly is not None else 0
        ),
        fallback_used=outcome.fallback_used,
    )


def _case_result(
    case: GoldenCase,
    *,
    baseline: RouteMeasurement,
    bounded: RouteMeasurement,
) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    baseline_hits = 0
    bounded_hits = 0
    for ordinal, (kind, path) in enumerate(case.expectations, start=1):
        baseline_match = baseline.ranks.get(path)
        bounded_match = bounded.ranks.get(path)
        baseline_hits += baseline_match is not None
        bounded_hits += bounded_match is not None
        matches.append(
            {
                "kind": kind,
                "ordinal": ordinal,
                "baseline_rank": baseline_match[0] if baseline_match else None,
                "baseline_docid": baseline_match[1] if baseline_match else None,
                "bounded_rank": bounded_match[0] if bounded_match else None,
                "bounded_docid": bounded_match[1] if bounded_match else None,
            }
        )
    reduction = 1 - (bounded.estimated_tokens / baseline.estimated_tokens)
    if not math.isfinite(reduction):
        raise _error(
            "golden_metric_invalid",
            f"Case {case.case_id!r} produced a non-finite context reduction.",
            "Repair the paired token measurements before persisting the run.",
        )
    return {
        "case_id": case.case_id,
        "expected_count": len(case.expectations),
        "baseline_hit_count": baseline_hits,
        "bounded_hit_count": bounded_hits,
        "fallback_used": bounded.fallback_used,
        "context_reduction": reduction,
        "matches": matches,
        "baseline": {
            "status": baseline.status,
            "docids": list(baseline.docids),
            "estimated_context_tokens": baseline.estimated_tokens,
        },
        "bounded": {
            "status": bounded.status,
            "docids": list(bounded.docids),
            "estimated_context_tokens": bounded.estimated_tokens,
        },
    }


def aggregate_case_results(cases: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    """Calculate paired aggregate metrics from metadata-only case results."""

    if not cases:
        raise ValueError("at least one golden case result is required")
    expected = sum(int(case["expected_count"]) for case in cases)
    if expected <= 0:
        raise ValueError("golden results require at least one expected artifact")
    hits = sum(int(case["bounded_hit_count"]) for case in cases)
    fallbacks = sum(bool(case["fallback_used"]) for case in cases)
    reductions = [float(case["context_reduction"]) for case in cases]
    return {
        "retrieval_hit_rate": hits / expected,
        "fallback_rate": fallbacks / len(cases),
        "median_context_reduction": median(reductions),
    }


def _resolve_golden_file(project_root: Path, relative_path: PurePosixPath) -> Path:
    root = project_root.resolve(strict=True)
    candidate = project_root.joinpath(*relative_path.parts)
    if candidate.is_symlink():
        raise _error(
            "golden_file_escape",
            "The visible golden file cannot be a symbolic link.",
            "Restore the versioned physical golden file beneath the project root.",
        )
    resolved = candidate.resolve(strict=False)
    if root not in resolved.parents:
        raise _error(
            "golden_file_escape",
            "The visible golden file escapes the current project.",
            "Keep golden.visible_path beneath the repository root.",
        )
    return resolved


def _new_run_id(now: datetime) -> str:
    timestamp = now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return f"run_{timestamp}_{secrets.token_hex(8)}"


def _format_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )


def run_golden_test(
    manifest_path: Path,
    *,
    bounded_runner: Callable[..., ContextOutcome] = run_context,
    occurred_at: datetime | None = None,
) -> GoldenTestOutcome:
    """Validate every input, preflight every baseline, then run bounded retrieval."""

    manifest: MemoryManifest = load_manifest(manifest_path)
    projection = load_projection(manifest_path)
    project_root = manifest_path.parent.parent
    golden_path = _resolve_golden_file(project_root, manifest.golden.visible_path)
    suite = load_golden_suite(golden_path)
    project_store = projection.stores.get("project")
    if project_store is None:
        raise _error(
            "golden_projection_missing",
            "The local project memory store is not configured.",
            "Run memory configure before memory test.",
        )

    # Preflight all baselines before the first QMD invocation (AC5).
    baselines = tuple(
        _measure_baseline(
            case,
            query=case.query,
            collection=manifest.stores.project.collection,
            root=project_store.root,
        )
        for case in suite.cases
    )
    case_results = tuple(
        _case_result(
            case,
            baseline=baseline,
            bounded=_measure_bounded(
                case,
                query=case.query,
                project_collection=manifest.stores.project.collection,
                runner=bounded_runner,
            ),
        )
        for case, baseline in zip(suite.cases, baselines, strict=True)
    )
    aggregate = aggregate_case_results(case_results)
    now = occurred_at or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("golden run timestamps must be timezone-aware")
    return GoldenTestOutcome(
        status="ready",
        exit_code=0,
        project_id=manifest.project.id,
        run_id=_new_run_id(now),
        occurred_at=_format_time(now),
        estimator_version=ESTIMATOR_VERSION,
        cases=case_results,
        aggregate=aggregate,
    )


def _run_projection(outcome: GoldenTestOutcome) -> dict[str, Any]:
    return {
        "schema_version": GOLDEN_RUN_SCHEMA_VERSION,
        "run_id": outcome.run_id,
        "occurred_at": outcome.occurred_at,
        "project_id": outcome.project_id,
        **outcome.data(),
    }


def persist_golden_run(
    outcome: GoldenTestOutcome,
    *,
    state_dir: Path,
    project_root: Path,
) -> tuple[Path, tuple[dict[str, str], ...]]:
    """Atomically persist one private metadata-only run JSON."""

    if _RUN_ID.fullmatch(outcome.run_id) is None:
        raise _error(
            "golden_run_id_invalid",
            "The golden run ID is invalid.",
            "Build runs through run_golden_test.",
            exit_code=50,
        )
    projection = _run_projection(outcome)
    try:
        scan_metadata_privacy(projection, field="run")
        root = validate_state_directory(state_dir, project_root)
        runs_root = root / "runs"
        project_dir = runs_root / outcome.project_id
        if runs_root.is_symlink() or project_dir.is_symlink():
            raise _error(
                "golden_run_store_escape",
                "The golden run directory cannot be a symbolic link.",
                "Restore a private physical runs directory beneath the state root.",
                exit_code=50,
            )
        resolved_runs = runs_root.resolve(strict=False)
        resolved_project = project_dir.resolve(strict=False)
        if resolved_runs not in resolved_project.parents:
            raise _error(
                "golden_run_store_escape",
                "The project run directory escapes the private runs root.",
                "Restore the private run directory and retry.",
                exit_code=50,
            )
        for directory in (root, runs_root, project_dir):
            ensure_private_state_directory(directory)
        path = project_dir / f"{outcome.run_id}.json"
        if path.exists() or path.is_symlink():
            raise _error(
                "golden_run_exists",
                "The immutable golden run ID already exists.",
                "Retry to allocate a fresh run ID.",
                exit_code=50,
            )
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{outcome.run_id}.", suffix=".tmp", dir=project_dir
        )
        temporary = Path(temporary_name)
        try:
            if os.name == "posix":
                os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(
                    projection,
                    stream,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(temporary, path)
            except FileExistsError as error:
                raise _error(
                    "golden_run_exists",
                    "The immutable golden run ID already exists.",
                    "Retry to allocate a fresh run ID.",
                    exit_code=50,
                ) from error
            if os.name == "posix":
                path.chmod(0o600)
            diagnostics = fsync_state_directory(project_dir)
        finally:
            if temporary.exists():
                temporary.unlink()
    except GoldenContractError:
        raise
    except EventIntegrityError as error:
        raise _error(
            "golden_run_privacy_violation",
            "The golden run violates the metadata-only persistence contract.",
            "Remove content-bearing, absolute-path or secret-shaped run fields.",
            exit_code=50,
        ) from error
    except OSError as error:
        raise _error(
            "golden_run_store_unavailable",
            "The metadata-only golden run could not be persisted safely.",
            "Restore access to the private memory state directory, then retry.",
            exit_code=50,
        ) from error
    run_diagnostics = tuple(
        {
            "code": "golden_run_directory_fsync_failed",
            "message": diagnostic["message"],
            "correction": diagnostic["correction"],
        }
        for diagnostic in diagnostics
    )
    return path, run_diagnostics
