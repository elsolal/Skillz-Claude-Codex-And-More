"""External quality rubric imports and the STORY-015 measurement gate."""

from __future__ import annotations

import json
import math
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, NoReturn

from .events import (
    EventIntegrityError,
    ensure_private_state_directory,
    fsync_state_directory,
    scan_metadata_privacy,
    validate_state_directory,
)
from .manifest import load_manifest
from .receipts import MeasurementGateOutcome, QualityRecordOutcome


QUALITY_RUBRIC_SCHEMA_VERSION = 1
QUALITY_IMPORT_SCHEMA_VERSION = 1
QUALITY_RECORD_SCHEMA_VERSION = 1
QUALITY_GATE_SCHEMA_VERSION = 1
QUALITY_MAX_DEGRADATION = 0.05
RETRIEVAL_MIN_HIT_RATE = 0.90
CONTEXT_MIN_REDUCTION = 0.50
REVIEWER_TYPES = frozenset({"human", "llm", "hybrid"})

_RUN_ID = re.compile(r"^run_\d{8}T\d{12}Z_[0-9a-f]{16}$")
_VERSION_ID = re.compile(r"^[a-z0-9][a-z0-9.-]{0,62}$")
_DIMENSION_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")


class QualityContractError(RuntimeError):
    """Stable rubric, import, gate or persistence contract failure."""

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
) -> QualityContractError:
    return QualityContractError(
        code=code,
        message=message,
        correction=correction,
        exit_code=exit_code,
    )


@dataclass(frozen=True, slots=True)
class QualityDimension:
    id: str
    weight: float


@dataclass(frozen=True, slots=True)
class QualityRubric:
    schema_version: int
    rubric_version: str
    minimum_score: float
    maximum_score: float
    dimensions: tuple[QualityDimension, ...]


@dataclass(frozen=True, slots=True)
class QualityImport:
    schema_version: int
    run_id: str
    rubric_version: str
    baseline_score: float
    score: float
    reviewer_type: str
    quality_degradation: float


def _strict_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate quality key: {key}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> NoReturn:
    raise ValueError(f"non-standard JSON constant: {value}")


def _read_json_object(path: Path, *, kind: str) -> dict[str, Any]:
    if path.is_symlink():
        raise _error(
            f"{kind}_file_escape",
            f"The {kind.replace('_', ' ')} file cannot be a symbolic link.",
            "Use a physical JSON file beneath an authorized local root.",
        )
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_strict_json_object,
            parse_constant=_reject_json_constant,
        )
    except FileNotFoundError as error:
        raise _error(
            f"{kind}_file_missing",
            f"The {kind.replace('_', ' ')} file is missing.",
            "Provide the expected strict JSON file and retry.",
        ) from error
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise _error(
            f"{kind}_file_invalid",
            f"The {kind.replace('_', ' ')} file is not strict readable JSON.",
            "Repair the JSON document and retry.",
        ) from error
    if not isinstance(payload, dict):
        raise _error(
            f"{kind}_schema_invalid",
            f"The {kind.replace('_', ' ')} root must be an object.",
            "Use the closed V1 object schema.",
        )
    return payload


def _exact_keys(
    value: Mapping[str, Any],
    *,
    expected: set[str],
    code: str,
    label: str,
) -> None:
    if set(value) != expected:
        raise _error(
            code,
            f"{label} does not match its closed V1 schema.",
            "Add every required field and remove unknown fields, including raw answers.",
        )


def _finite_number(value: object, field: str, *, code: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _error(code, f"{field} must be numeric.", "Use a finite JSON number.")
    number = float(value)
    if not math.isfinite(number):
        raise _error(code, f"{field} must be finite.", "Remove NaN or infinity.")
    return number


def load_quality_rubric(path: Path) -> QualityRubric:
    """Load the versioned scoring contract without evaluating any response."""

    payload = _read_json_object(path, kind="quality_rubric")
    _exact_keys(
        payload,
        expected={"schema_version", "rubric_version", "score", "dimensions"},
        code="quality_rubric_schema_invalid",
        label="Quality rubric",
    )
    if payload["schema_version"] != QUALITY_RUBRIC_SCHEMA_VERSION:
        raise _error(
            "quality_rubric_schema_unknown",
            "The quality rubric uses an unknown schema version.",
            f"Use schema version {QUALITY_RUBRIC_SCHEMA_VERSION}.",
        )
    version = payload["rubric_version"]
    if not isinstance(version, str) or _VERSION_ID.fullmatch(version) is None:
        raise _error(
            "quality_rubric_version_invalid",
            "rubric_version must be a stable lowercase identifier.",
            "Use lowercase letters, digits, dots or hyphens.",
        )
    score = payload["score"]
    if not isinstance(score, dict):
        raise _error(
            "quality_rubric_schema_invalid",
            "Quality rubric score must be an object.",
            "Declare numeric minimum and maximum fields.",
        )
    _exact_keys(
        score,
        expected={"minimum", "maximum"},
        code="quality_rubric_schema_invalid",
        label="Quality rubric score",
    )
    minimum = _finite_number(
        score["minimum"], "score.minimum", code="quality_rubric_score_invalid"
    )
    maximum = _finite_number(
        score["maximum"], "score.maximum", code="quality_rubric_score_invalid"
    )
    if minimum >= maximum:
        raise _error(
            "quality_rubric_score_invalid",
            "Quality rubric score minimum must stay below maximum.",
            "Declare one non-empty deterministic score range.",
        )

    raw_dimensions = payload["dimensions"]
    if not isinstance(raw_dimensions, list) or not raw_dimensions:
        raise _error(
            "quality_rubric_dimensions_invalid",
            "Quality rubric dimensions must be a non-empty array.",
            "Declare weighted V1 dimensions whose weights sum to 1.",
        )
    dimensions: list[QualityDimension] = []
    for index, raw in enumerate(raw_dimensions):
        if not isinstance(raw, dict):
            raise _error(
                "quality_rubric_dimensions_invalid",
                f"dimensions[{index}] must be an object.",
                "Declare id and weight for every dimension.",
            )
        _exact_keys(
            raw,
            expected={"id", "weight"},
            code="quality_rubric_dimensions_invalid",
            label=f"dimensions[{index}]",
        )
        dimension_id = raw["id"]
        if (
            not isinstance(dimension_id, str)
            or _DIMENSION_ID.fullmatch(dimension_id) is None
        ):
            raise _error(
                "quality_rubric_dimensions_invalid",
                f"dimensions[{index}].id is invalid.",
                "Use a stable lowercase kebab-case dimension ID.",
            )
        weight = _finite_number(
            raw["weight"],
            f"dimensions[{index}].weight",
            code="quality_rubric_dimensions_invalid",
        )
        if weight <= 0:
            raise _error(
                "quality_rubric_dimensions_invalid",
                f"dimensions[{index}].weight must be positive.",
                "Use positive weights that sum to 1.",
            )
        dimensions.append(QualityDimension(id=dimension_id, weight=weight))
    ids = [dimension.id for dimension in dimensions]
    if len(ids) != len(set(ids)) or not math.isclose(
        sum(dimension.weight for dimension in dimensions),
        1.0,
        rel_tol=0.0,
        abs_tol=1e-9,
    ):
        raise _error(
            "quality_rubric_dimensions_invalid",
            "Quality rubric dimension IDs must be unique and weights must sum to 1.",
            "Deduplicate IDs and normalize the V1 weights.",
        )
    return QualityRubric(
        schema_version=QUALITY_RUBRIC_SCHEMA_VERSION,
        rubric_version=version,
        minimum_score=minimum,
        maximum_score=maximum,
        dimensions=tuple(dimensions),
    )


def calculate_quality_degradation(baseline_score: float, score: float) -> float:
    """Return relative degradation; improvements never become negative failures."""

    baseline = _finite_number(
        baseline_score, "baseline_score", code="quality_baseline_invalid"
    )
    candidate = _finite_number(score, "score", code="quality_score_invalid")
    if baseline <= 0:
        raise _error(
            "quality_baseline_invalid",
            "baseline_score must be greater than zero for relative comparison.",
            "Import a positive externally evaluated baseline score.",
        )
    return max(0.0, (baseline - candidate) / baseline)


def load_quality_import(path: Path, *, rubric: QualityRubric) -> QualityImport:
    """Validate a closed metadata-only score import against its rubric."""

    payload = _read_json_object(path, kind="quality_import")
    _exact_keys(
        payload,
        expected={
            "schema_version",
            "run_id",
            "rubric_version",
            "baseline_score",
            "score",
            "reviewer_type",
        },
        code="quality_import_schema_invalid",
        label="Quality import",
    )
    if payload["schema_version"] != QUALITY_IMPORT_SCHEMA_VERSION:
        raise _error(
            "quality_import_schema_unknown",
            "The quality import uses an unknown schema version.",
            f"Use schema version {QUALITY_IMPORT_SCHEMA_VERSION}.",
        )
    run_id = payload["run_id"]
    if not isinstance(run_id, str) or _RUN_ID.fullmatch(run_id) is None:
        raise _error(
            "quality_run_id_invalid",
            "The imported run_id is invalid.",
            "Use the immutable run_id emitted by memory test --holdout.",
        )
    rubric_version = payload["rubric_version"]
    if rubric_version != rubric.rubric_version:
        raise _error(
            "quality_rubric_version_mismatch",
            "The imported rubric_version does not match the manifest rubric.",
            f"Evaluate with rubric {rubric.rubric_version!r} and re-export the score.",
        )
    reviewer_type = payload["reviewer_type"]
    if not isinstance(reviewer_type, str) or reviewer_type not in REVIEWER_TYPES:
        raise _error(
            "quality_reviewer_invalid",
            "reviewer_type is not a V1 provenance value.",
            "Use human, llm or hybrid.",
        )
    baseline_score = _finite_number(
        payload["baseline_score"],
        "baseline_score",
        code="quality_baseline_invalid",
    )
    score = _finite_number(payload["score"], "score", code="quality_score_invalid")
    if not (
        rubric.minimum_score <= baseline_score <= rubric.maximum_score
        and rubric.minimum_score <= score <= rubric.maximum_score
    ):
        raise _error(
            "quality_score_out_of_range",
            "Imported scores fall outside the versioned rubric range.",
            "Re-export both scores using the declared minimum and maximum.",
        )
    degradation = calculate_quality_degradation(baseline_score, score)
    return QualityImport(
        schema_version=QUALITY_IMPORT_SCHEMA_VERSION,
        run_id=run_id,
        rubric_version=rubric_version,
        baseline_score=baseline_score,
        score=score,
        reviewer_type=reviewer_type,
        quality_degradation=degradation,
    )


def _validate_record_location(
    *,
    state_dir: Path,
    project_root: Path,
    project_id: str,
    category: str,
) -> tuple[Path, Path, Path]:
    if _DIMENSION_ID.fullmatch(project_id) is None:
        raise _error(
            "quality_project_id_invalid",
            "The quality record project_id is invalid.",
            "Use the validated lowercase project ID from the memory manifest.",
            exit_code=50,
        )
    try:
        root = validate_state_directory(state_dir, project_root)
    except EventIntegrityError as error:
        raise _error(
            "quality_record_store_invalid",
            "The quality record state directory is unsafe.",
            "Choose a private state directory outside the current project.",
            exit_code=50,
        ) from error
    category_root = root / category
    project_dir = category_root / project_id
    if category_root.is_symlink() or project_dir.is_symlink():
        raise _error(
            "quality_record_store_escape",
            "The quality record directory cannot be a symbolic link.",
            "Restore a private physical directory beneath the state root.",
            exit_code=50,
        )
    if category_root.resolve(strict=False) not in project_dir.resolve(strict=False).parents:
        raise _error(
            "quality_record_store_escape",
            "The quality project directory escapes its private record root.",
            "Restore the private state directory and retry.",
            exit_code=50,
        )
    return root, category_root, project_dir


def _validate_source_run(
    *,
    run_id: str,
    project_id: str,
    state_dir: Path,
    project_root: Path,
) -> dict[str, Any]:
    _, _, run_dir = _validate_record_location(
        state_dir=state_dir,
        project_root=project_root,
        project_id=project_id,
        category="runs",
    )
    path = run_dir / f"{run_id}.json"
    if path.is_symlink():
        raise _error(
            "quality_run_store_escape",
            "The referenced golden run cannot be a symbolic link.",
            "Restore the physical immutable run before importing quality.",
            exit_code=50,
        )
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_strict_json_object,
            parse_constant=_reject_json_constant,
        )
    except FileNotFoundError as error:
        raise _error(
            "quality_run_missing",
            "The quality import references an unknown golden run.",
            "Run memory test --holdout and import against its emitted run_id.",
        ) from error
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise _error(
            "quality_run_invalid",
            "The referenced golden run is not readable strict JSON.",
            "Restore the immutable metadata-only run and retry.",
            exit_code=50,
        ) from error
    if (
        not isinstance(payload, dict)
        or payload.get("run_id") != run_id
        or payload.get("project_id") != project_id
        or not isinstance(payload.get("aggregate"), dict)
    ):
        raise _error(
            "quality_run_invalid",
            "The referenced golden run identity or aggregate is invalid.",
            "Use an unmodified run emitted for the current project.",
            exit_code=50,
        )
    return payload


def _quality_projection(imported: QualityImport, *, project_id: str) -> dict[str, object]:
    return {
        "schema_version": QUALITY_RECORD_SCHEMA_VERSION,
        "project_id": project_id,
        "run_id": imported.run_id,
        "rubric_version": imported.rubric_version,
        "baseline_score": imported.baseline_score,
        "score": imported.score,
        "reviewer_type": imported.reviewer_type,
        "quality_degradation": imported.quality_degradation,
    }


def persist_quality_import(
    imported: QualityImport,
    *,
    project_id: str,
    state_dir: Path,
    project_root: Path,
) -> tuple[Path, tuple[dict[str, str], ...]]:
    """Publish one immutable metadata-only quality record for an existing run."""

    if _RUN_ID.fullmatch(imported.run_id) is None:
        raise _error(
            "quality_run_id_invalid",
            "The imported run_id is invalid.",
            "Use a run_id emitted by memory test --holdout.",
            exit_code=50,
        )
    _validate_source_run(
        run_id=imported.run_id,
        project_id=project_id,
        state_dir=state_dir,
        project_root=project_root,
    )
    projection = _quality_projection(imported, project_id=project_id)
    try:
        scan_metadata_privacy(projection, field="quality_record")
        root, quality_root, project_dir = _validate_record_location(
            state_dir=state_dir,
            project_root=project_root,
            project_id=project_id,
            category="quality",
        )
        for directory in (root, quality_root, project_dir):
            ensure_private_state_directory(directory)
        path = project_dir / f"{imported.run_id}.json"
        if path.exists() or path.is_symlink():
            raise _error(
                "quality_record_exists",
                "An immutable quality record already exists for this run.",
                "Use a new golden run for a new external evaluation.",
                exit_code=50,
            )
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{imported.run_id}.", suffix=".tmp", dir=project_dir
        )
        temporary = Path(temporary_name)
        published = False
        cleanup_diagnostics: list[dict[str, str]] = []
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                if os.name == "posix":
                    os.fchmod(stream.fileno(), 0o600)
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
                published = True
            except FileExistsError as error:
                raise _error(
                    "quality_record_exists",
                    "An immutable quality record already exists for this run.",
                    "Use a new golden run for a new external evaluation.",
                    exit_code=50,
                ) from error
            try:
                temporary.unlink()
            except OSError as error:
                cleanup_diagnostics.append(
                    {
                        "code": "quality_record_temp_cleanup_failed",
                        "message": (
                            "The immutable quality record was published, but its "
                            "private temporary link could not be removed."
                        ),
                        "correction": (
                            "Remove the private temporary quality link and verify "
                            f"state directory permissions ({error.__class__.__name__})."
                        ),
                    }
                )
            durability_diagnostics = fsync_state_directory(project_dir)
        finally:
            if not published and temporary.exists():
                try:
                    temporary.unlink()
                except OSError:
                    pass
    except QualityContractError:
        raise
    except EventIntegrityError as error:
        raise _error(
            "quality_record_privacy_violation",
            "The imported quality record violates the metadata-only contract.",
            "Remove content-bearing, absolute-path or secret-shaped fields.",
            exit_code=50,
        ) from error
    except OSError as error:
        raise _error(
            "quality_record_store_unavailable",
            "The quality record could not be persisted safely.",
            "Restore access to the private memory state directory, then retry.",
            exit_code=50,
        ) from error
    diagnostics = tuple(cleanup_diagnostics) + tuple(
        {
            "code": "quality_record_directory_fsync_failed",
            "message": diagnostic["message"],
            "correction": diagnostic["correction"],
        }
        for diagnostic in durability_diagnostics
    )
    return path, diagnostics


def load_quality_record(
    *,
    run_id: str,
    project_id: str,
    state_dir: Path,
    project_root: Path,
) -> dict[str, Any]:
    """Read and validate the immutable quality projection consumed by the gate."""

    _, _, project_dir = _validate_record_location(
        state_dir=state_dir,
        project_root=project_root,
        project_id=project_id,
        category="quality",
    )
    path = project_dir / f"{run_id}.json"
    if path.is_symlink():
        raise _error(
            "quality_record_store_escape",
            "The quality record cannot be a symbolic link.",
            "Restore the physical immutable quality record.",
            exit_code=50,
        )
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_strict_json_object,
            parse_constant=_reject_json_constant,
        )
    except FileNotFoundError as error:
        raise _error(
            "quality_record_missing",
            "No imported quality record exists for this run.",
            "Run memory test record-quality before requesting the gate.",
        ) from error
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise _error(
            "quality_record_invalid",
            "The immutable quality record is not readable strict JSON.",
            "Restore or replace it through a new golden run.",
            exit_code=50,
        ) from error
    expected = {
        "schema_version",
        "project_id",
        "run_id",
        "rubric_version",
        "baseline_score",
        "score",
        "reviewer_type",
        "quality_degradation",
    }
    if not isinstance(payload, dict) or set(payload) != expected:
        raise _error(
            "quality_record_invalid",
            "The immutable quality record does not match the closed V1 schema.",
            "Use a record produced by memory test record-quality.",
            exit_code=50,
        )
    if (
        payload["schema_version"] != QUALITY_RECORD_SCHEMA_VERSION
        or payload["project_id"] != project_id
        or payload["run_id"] != run_id
        or payload["reviewer_type"] not in REVIEWER_TYPES
    ):
        raise _error(
            "quality_record_invalid",
            "The immutable quality record identity or provenance is invalid.",
            "Use the record linked to the current project and run.",
            exit_code=50,
        )
    _finite_number(
        payload["quality_degradation"],
        "quality_degradation",
        code="quality_record_invalid",
    )
    try:
        scan_metadata_privacy(payload, field="quality_record")
    except EventIntegrityError as error:
        raise _error(
            "quality_record_privacy_violation",
            "The immutable quality record violates the metadata-only contract.",
            "Remove the record and re-evaluate through a new golden run.",
            exit_code=50,
        ) from error
    return payload


def _dimension(status: str, value: float | int | None, threshold: object) -> dict[str, object]:
    return {"status": status, "value": value, "threshold": threshold}


def evaluate_measurement_gate(
    *,
    aggregate: Mapping[str, object],
    holdout_case_count: int,
    quality_degradation: float | None,
) -> dict[str, object]:
    """Evaluate the STORY-015 slice; a pass never authorizes global rollout."""

    retrieval = _finite_number(
        aggregate.get("retrieval_hit_rate"),
        "aggregate.retrieval_hit_rate",
        code="quality_gate_metric_invalid",
    )
    context = _finite_number(
        aggregate.get("median_context_reduction"),
        "aggregate.median_context_reduction",
        code="quality_gate_metric_invalid",
    )
    if isinstance(holdout_case_count, bool) or not isinstance(holdout_case_count, int):
        raise _error(
            "quality_gate_metric_invalid",
            "holdout_case_count must be an integer.",
            "Load the count from an immutable golden run.",
            exit_code=50,
        )

    dimensions: dict[str, dict[str, object]] = {
        "holdout": _dimension(
            "pass" if holdout_case_count == 2 else "incomplete",
            holdout_case_count,
            {"minimum_ratio": 0.20, "required_cases": 2},
        ),
        "retrieval": _dimension(
            "pass" if retrieval >= RETRIEVAL_MIN_HIT_RATE else "fail",
            retrieval,
            {"minimum": RETRIEVAL_MIN_HIT_RATE},
        ),
        "context": _dimension(
            "pass" if context >= CONTEXT_MIN_REDUCTION else "fail",
            context,
            {"minimum_reduction": CONTEXT_MIN_REDUCTION},
        ),
    }
    if quality_degradation is None:
        dimensions["quality"] = _dimension(
            "incomplete",
            None,
            {"maximum_degradation": QUALITY_MAX_DEGRADATION},
        )
    else:
        degradation = _finite_number(
            quality_degradation,
            "quality_degradation",
            code="quality_gate_metric_invalid",
        )
        dimensions["quality"] = _dimension(
            "pass" if degradation <= QUALITY_MAX_DEGRADATION else "fail",
            degradation,
            {"maximum_degradation": QUALITY_MAX_DEGRADATION},
        )

    statuses = {str(dimension["status"]) for dimension in dimensions.values()}
    status = "fail" if "fail" in statuses else "incomplete" if "incomplete" in statuses else "pass"
    return {
        "schema_version": QUALITY_GATE_SCHEMA_VERSION,
        "scope": "story-015-measurement",
        "status": status,
        "authorizes_global_rollout": False,
        "dimensions": dimensions,
    }


def _resolve_project_file(project_root: Path, relative_path: object, *, label: str) -> Path:
    root = project_root.resolve(strict=True)
    parts = getattr(relative_path, "parts", ())
    candidate = project_root.joinpath(*parts)
    if candidate.is_symlink():
        raise _error(
            f"{label}_file_escape",
            f"The {label.replace('_', ' ')} file cannot be a symbolic link.",
            "Restore the versioned physical file beneath the project root.",
        )
    resolved = candidate.resolve(strict=False)
    if root not in resolved.parents:
        raise _error(
            f"{label}_file_escape",
            f"The {label.replace('_', ' ')} file escapes the current project.",
            "Keep the manifest-declared file beneath the repository root.",
        )
    return resolved


def record_quality_from_file(
    manifest_path: Path,
    *,
    input_path: Path,
    state_dir: Path,
) -> QualityRecordOutcome:
    """Validate and persist one external score without reading any raw response."""

    manifest = load_manifest(manifest_path)
    project_root = manifest_path.parent.parent
    rubric_path = _resolve_project_file(
        project_root,
        manifest.golden.quality_rubric,
        label="quality_rubric",
    )
    rubric = load_quality_rubric(rubric_path)
    imported = load_quality_import(input_path, rubric=rubric)
    _, diagnostics = persist_quality_import(
        imported,
        project_id=manifest.project.id,
        state_dir=state_dir,
        project_root=project_root,
    )
    return QualityRecordOutcome(
        status="degraded" if diagnostics else "ready",
        exit_code=50 if diagnostics else 0,
        project_id=manifest.project.id,
        run_id=imported.run_id,
        rubric_version=imported.rubric_version,
        baseline_score=imported.baseline_score,
        score=imported.score,
        reviewer_type=imported.reviewer_type,
        quality_degradation=imported.quality_degradation,
        errors=diagnostics,
    )


def run_measurement_gate(
    manifest_path: Path,
    *,
    run_id: str,
    state_dir: Path,
) -> MeasurementGateOutcome:
    """Combine an immutable holdout run with its optional external quality record."""

    manifest = load_manifest(manifest_path)
    project_root = manifest_path.parent.parent
    run = _validate_source_run(
        run_id=run_id,
        project_id=manifest.project.id,
        state_dir=state_dir,
        project_root=project_root,
    )
    quality_degradation: float | None = None
    quality_path = state_dir.resolve(strict=False) / "quality" / manifest.project.id / f"{run_id}.json"
    if quality_path.exists() or quality_path.is_symlink():
        rubric_path = _resolve_project_file(
            project_root,
            manifest.golden.quality_rubric,
            label="quality_rubric",
        )
        rubric = load_quality_rubric(rubric_path)
        quality = load_quality_record(
            run_id=run_id,
            project_id=manifest.project.id,
            state_dir=state_dir,
            project_root=project_root,
        )
        if quality["rubric_version"] != rubric.rubric_version:
            raise _error(
                "quality_record_rubric_stale",
                "The quality record does not use the current versioned rubric.",
                "Create a new golden run and evaluate it with the current rubric.",
            )
        quality_degradation = float(quality["quality_degradation"])

    holdout = run.get("holdout")
    holdout_case_count = (
        int(holdout.get("case_count", 0)) if isinstance(holdout, dict) else 0
    )
    aggregate = run["aggregate"]
    assert isinstance(aggregate, dict)
    gate = evaluate_measurement_gate(
        aggregate=aggregate,
        holdout_case_count=holdout_case_count,
        quality_degradation=quality_degradation,
    )
    status = str(gate["status"])
    return MeasurementGateOutcome(
        status=status,
        exit_code=0 if status == "pass" else 10 if status == "incomplete" else 20,
        project_id=manifest.project.id,
        run_id=run_id,
        gate=gate,
    )
