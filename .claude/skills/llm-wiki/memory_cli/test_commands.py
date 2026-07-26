"""CLI orchestration for golden, holdout, external quality, and measurement gates."""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

from .contracts import PUBLIC_SCHEMA_VERSION
from .events import resolve_state_dir
from .golden import GoldenContractError, persist_golden_run, run_golden_test
from .manifest import ManifestError, discover_manifest, load_manifest
from .measurement import record_quality_from_file, run_measurement_gate
from .projection import ProjectionError
from .quality import QualityContractError
from .render_human import (
    render_golden_test_human,
    render_measurement_gate_human,
    render_quality_record_human,
)
from .render_json import (
    render_golden_test_json,
    render_measurement_gate_json,
    render_quality_record_json,
)


def _render_blocked(
    *,
    command: str,
    error: object,
    json_output: bool,
    project_id: str | None,
    run_id: str | None,
) -> int:
    code = str(getattr(error, "code"))
    message = str(getattr(error, "message"))
    correction = str(getattr(error, "correction"))
    exit_code = int(getattr(error, "exit_code"))
    if json_output:
        print(
            json.dumps(
                {
                    "schema_version": PUBLIC_SCHEMA_VERSION,
                    "command": command,
                    "status": "blocked",
                    "project_id": project_id,
                    "run_id": run_id,
                    "data": {},
                    "warnings": [],
                    "errors": [
                        {"code": code, "message": message, "correction": correction}
                    ],
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
    else:
        label = command.replace(".", " ")
        print(f"[blocked] memory {label} · {code}")
        print(message)
        print(f"Correction: {correction}")
    return exit_code


def run_golden_command(*, include_holdout: bool, json_output: bool) -> int:
    project_id: str | None = None
    try:
        manifest_path = discover_manifest()
        manifest = load_manifest(manifest_path)
        project_id = manifest.project.id
        outcome = run_golden_test(manifest_path, include_holdout=include_holdout)
        _, persistence_diagnostics = persist_golden_run(
            outcome,
            state_dir=resolve_state_dir(),
            project_root=manifest_path.parent.parent,
        )
        if persistence_diagnostics:
            outcome = replace(
                outcome,
                exit_code=50,
                errors=(*outcome.errors, *persistence_diagnostics),
            )
    except (ManifestError, ProjectionError, GoldenContractError) as error:
        return _render_blocked(
            command="test",
            error=error,
            json_output=json_output,
            project_id=project_id,
            run_id=None,
        )
    if json_output:
        render_golden_test_json(outcome, stream=sys.stdout)
    else:
        render_golden_test_human(outcome, stream=sys.stdout)
    return outcome.exit_code


def run_record_quality_command(*, input_path: str, json_output: bool) -> int:
    project_id: str | None = None
    try:
        manifest_path = discover_manifest()
        manifest = load_manifest(manifest_path)
        project_id = manifest.project.id
        outcome = record_quality_from_file(
            manifest_path,
            input_path=Path(input_path),
            state_dir=resolve_state_dir(),
        )
    except (ManifestError, QualityContractError) as error:
        return _render_blocked(
            command="test.record-quality",
            error=error,
            json_output=json_output,
            project_id=project_id,
            run_id=None,
        )
    if json_output:
        render_quality_record_json(outcome, stream=sys.stdout)
    else:
        render_quality_record_human(outcome, stream=sys.stdout)
    return outcome.exit_code


def run_measurement_gate_command(*, run_id: str, json_output: bool) -> int:
    project_id: str | None = None
    try:
        manifest_path = discover_manifest()
        manifest = load_manifest(manifest_path)
        project_id = manifest.project.id
        outcome = run_measurement_gate(
            manifest_path,
            run_id=run_id,
            state_dir=resolve_state_dir(),
        )
    except (ManifestError, QualityContractError) as error:
        return _render_blocked(
            command="test.gate",
            error=error,
            json_output=json_output,
            project_id=project_id,
            run_id=run_id,
        )
    if json_output:
        render_measurement_gate_json(outcome, stream=sys.stdout)
    else:
        render_measurement_gate_human(outcome, stream=sys.stdout)
    return outcome.exit_code
