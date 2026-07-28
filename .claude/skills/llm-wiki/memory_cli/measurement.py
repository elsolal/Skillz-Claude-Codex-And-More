"""High-level STORY-015 quality import and measurement-gate orchestration."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .manifest import load_manifest
from .quality import (
    _error,
    _validate_source_run,
    evaluate_measurement_gate,
    load_quality_import,
    load_quality_record,
    load_quality_rubric,
    persist_quality_import,
)
from .receipts import MeasurementGateOutcome, QualityRecordOutcome


def read_project_measurements(
    *,
    project_id: str,
    state_dir: Path,
    project_root: Path,
) -> tuple[tuple[dict[str, object], ...], tuple[dict[str, object], ...]]:
    """Load validated immutable runs and their optional quality records."""

    runs_dir = state_dir.resolve(strict=False) / "runs" / project_id
    if not runs_dir.exists():
        return (), ()
    if runs_dir.is_symlink():
        raise _error(
            "quality_run_store_escape",
            "The project run directory cannot be a symbolic link.",
            "Restore the physical private run directory.",
            exit_code=50,
        )
    runs: list[dict[str, object]] = []
    quality_records: list[dict[str, object]] = []
    for path in sorted(runs_dir.glob("*.json")):
        run = _validate_source_run(
            run_id=path.stem,
            project_id=project_id,
            state_dir=state_dir,
            project_root=project_root,
        )
        occurred_at = run.get("occurred_at")
        try:
            if not isinstance(occurred_at, str):
                raise ValueError
            datetime.fromisoformat(
                f"{occurred_at[:-1]}+00:00"
                if occurred_at.endswith("Z")
                else occurred_at
            )
        except ValueError as error:
            raise _error(
                "quality_run_invalid",
                "The referenced golden run timestamp is invalid.",
                "Use an unmodified run emitted by memory test.",
                exit_code=50,
            ) from error
        runs.append(run)
        quality_path = (
            state_dir.resolve(strict=False)
            / "quality"
            / project_id
            / f"{path.stem}.json"
        )
        if quality_path.exists() or quality_path.is_symlink():
            quality_records.append(
                load_quality_record(
                    run_id=path.stem,
                    project_id=project_id,
                    state_dir=state_dir,
                    project_root=project_root,
                )
            )
    return tuple(runs), tuple(quality_records)


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
    rubric_path = _resolve_project_file(
        project_root,
        manifest.golden.quality_rubric,
        label="quality_rubric",
    )
    rubric = load_quality_rubric(rubric_path)
    run = _validate_source_run(
        run_id=run_id,
        project_id=manifest.project.id,
        state_dir=state_dir,
        project_root=project_root,
    )
    quality_degradation: float | None = None
    quality_path = (
        state_dir.resolve(strict=False)
        / "quality"
        / manifest.project.id
        / f"{run_id}.json"
    )
    if quality_path.exists() or quality_path.is_symlink():
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
        baseline_score = float(quality["baseline_score"])
        score = float(quality["score"])
        if not (
            rubric.minimum_score <= baseline_score <= rubric.maximum_score
            and rubric.minimum_score <= score <= rubric.maximum_score
        ):
            raise _error(
                "quality_record_invalid",
                "The quality record scores fall outside the current rubric range.",
                "Create a new golden run and evaluate it with the current rubric.",
                exit_code=50,
            )
        quality_degradation = float(quality["quality_degradation"])

    holdout = run.get("holdout")
    holdout_case_count = holdout["case_count"] if isinstance(holdout, dict) else 0
    assert isinstance(holdout_case_count, int)
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
