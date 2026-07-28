"""Filesystem orchestration for STORY-016 weekly reports."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

from .contracts import PUBLIC_SCHEMA_VERSION
from .events import (
    EventIntegrityError,
    read_project_events,
    resolve_state_dir,
    scan_metadata_privacy,
)
from .manifest import ManifestError, discover_manifest, load_manifest
from .measurement import read_project_measurements
from .quality import QualityContractError
from .render_human import render_weekly_report_human
from .render_json import render_weekly_report_json
from .render_markdown import (
    ReportExportError,
    render_weekly_report_markdown,
)
from .report import build_weekly_report


def _write_markdown_atomically(path: Path, markdown: str) -> None:
    if path.is_symlink():
        raise ReportExportError(
            code="report_export_path_unsafe",
            message="The Markdown export target cannot be a symbolic link.",
            correction="Choose a physical local Markdown file.",
        )
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write(markdown)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if temporary.exists():
                temporary.unlink()
    except ReportExportError:
        raise
    except OSError as error:
        raise ReportExportError(
            code="report_export_unavailable",
            message="The Markdown report could not be written atomically.",
            correction="Restore access to the selected local export directory.",
        ) from error


def _render_blocked(
    *,
    json_output: bool,
    project_id: str | None,
    error: ManifestError | EventIntegrityError | QualityContractError | ReportExportError,
) -> int:
    if json_output:
        print(
            json.dumps(
                {
                    "schema_version": PUBLIC_SCHEMA_VERSION,
                    "command": "report.weekly",
                    "status": "blocked",
                    "project_id": project_id,
                    "data": {},
                    "warnings": [],
                    "errors": [error.as_dict()],
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
    else:
        print(f"[blocked] memory report · {error.code}")
        print(error.message)
        print(f"Correction: {error.correction}")
    return error.exit_code


def run_weekly_report_command(
    *,
    json_output: bool,
    export_markdown: str | None,
) -> int:
    project_id: str | None = None
    try:
        manifest_path = discover_manifest()
        manifest = load_manifest(manifest_path)
        project_id = manifest.project.id
        project_root = manifest_path.parent.parent
        state_dir = resolve_state_dir()
        event_result = read_project_events(
            project_id,
            state_dir=state_dir,
            project_root=project_root,
        )
        runs, quality_records = read_project_measurements(
            project_id=project_id,
            state_dir=state_dir,
            project_root=project_root,
        )
        outcome = build_weekly_report(
            project_id=project_id,
            events=event_result.events,
            runs=runs,
            quality_records=quality_records,
            warnings=event_result.diagnostics,
        )
        scan_metadata_privacy(outcome.data(), field="weekly_report")
        if export_markdown is not None:
            markdown = render_weekly_report_markdown(outcome)
            _write_markdown_atomically(Path(export_markdown).expanduser(), markdown)
    except (ManifestError, EventIntegrityError, QualityContractError, ReportExportError) as error:
        return _render_blocked(
            json_output=json_output,
            project_id=project_id,
            error=error,
        )

    if json_output:
        render_weekly_report_json(outcome, stream=sys.stdout)
    else:
        render_weekly_report_human(outcome, stream=sys.stdout)
        if export_markdown is not None:
            print(f"Markdown export: {Path(export_markdown).expanduser()}")
    return outcome.exit_code
