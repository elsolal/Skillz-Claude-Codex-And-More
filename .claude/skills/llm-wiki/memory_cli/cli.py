"""Argument parsing and rendering for the portable memory CLI."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from typing import Any

from . import __version__
from .contracts import PUBLIC_SCHEMA_VERSION, MemoryManifest, PrincipalRole
from .manifest import ManifestError, discover_manifest, load_manifest, load_nearest_manifest
from .projection import ConfigureOutcome, ProjectionError, configure_projection


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="memory",
        description="Portable Skillz-Claude memory control plane.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"skillz-memory {__version__}",
    )
    commands = parser.add_subparsers(dest="command")
    manifest_parser = commands.add_parser(
        "manifest",
        help="Discover and validate the nearest portable memory manifest.",
    )
    manifest_parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit the stable machine-readable result envelope.",
    )
    configure_parser = commands.add_parser(
        "configure",
        help="Create the ignored local projection and project-memory pointers.",
    )
    configure_parser.add_argument(
        "--store",
        action="append",
        required=True,
        dest="stores",
        metavar="NAME=PATH",
        help="Map a logical store to an absolute local root (V1 requires project=PATH).",
    )
    configure_parser.add_argument(
        "--role",
        choices=[role.value for role in PrincipalRole],
        default=PrincipalRole.COLLABORATOR.value,
        help="Declare the local principal role; this never grants access (default: collaborator).",
    )
    configure_parser.add_argument(
        "--replace-managed",
        action="store_true",
        help="Explicitly replace divergent project-memory pointers with managed content.",
    )
    configure_parser.add_argument(
        "--explain-local-paths",
        action="store_true",
        help="Include absolute machine-local paths in this local command output.",
    )
    configure_parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit the stable machine-readable result envelope.",
    )
    return parser


def _envelope(
    *,
    command: str,
    status: str,
    project_id: str | None,
    data: dict[str, Any],
    warnings: list[dict[str, Any]] | None = None,
    errors: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": PUBLIC_SCHEMA_VERSION,
        "command": command,
        "status": status,
        "project_id": project_id,
        "event_id": None,
        "data": data,
        "warnings": warnings or [],
        "errors": errors or [],
    }


def _manifest_data(manifest: MemoryManifest) -> dict[str, Any]:
    return {
        "manifest_schema_version": manifest.schema_version,
        "project": {
            "id": manifest.project.id,
            "name": manifest.project.name,
            "owner": manifest.project.owner,
        },
        "stores": {
            "project": {
                "remote": manifest.stores.project.remote,
                "collection": manifest.stores.project.collection,
                "entry_pages": [str(path) for path in manifest.stores.project.entry_pages],
            }
        },
        "fallbacks": [
            {
                "id": fallback.id,
                "collection": fallback.collection,
                "allowed_roles": [role.value for role in fallback.allowed_roles],
                "task_categories": [category.value for category in fallback.task_categories],
                "entry_pages": [str(path) for path in fallback.entry_pages],
            }
            for fallback in manifest.fallbacks
        ],
        "budgets": {
            mode.value: {
                "target_tokens": budget.target_tokens,
                "hard_tokens": budget.hard_tokens,
            }
            for mode, budget in manifest.budgets.items()
        },
        "policy": {
            "semantic_retrieval": manifest.policy.semantic_retrieval.value,
            "full_index_fallback": manifest.policy.full_index_fallback,
            "retention_days": manifest.policy.retention_days,
        },
        "golden": {
            "visible_path": str(manifest.golden.visible_path),
            "quality_rubric": str(manifest.golden.quality_rubric),
        },
    }


def _render_json(result: dict[str, Any]) -> None:
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))


def _render_manifest_human(manifest: MemoryManifest) -> None:
    print(f"[ok] manifest       .agents/memory.yaml · schema v{manifest.schema_version}")
    print(f"[ok] project        {manifest.project.name} · {manifest.project.id}")
    print(f"[ok] project store  {manifest.stores.project.collection}")
    print(f"[ok] entry pages    {len(manifest.stores.project.entry_pages)} declared")
    print(f"[ok] fallbacks      {len(manifest.fallbacks)} declared")


def _render_error_human(error: ManifestError) -> None:
    print(f"[blocked] manifest · {error.code}")
    print(f"Field: {error.field}")
    print(error.message)
    print(f"Correction: {error.correction}")


def _configure_data(
    outcome: ConfigureOutcome,
    *,
    explain_local_paths: bool,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "principal": {"role": outcome.projection.principal_role.value},
        "configured_stores": list(outcome.projection.stores),
        "local_files": [
            path.relative_to(outcome.project_root).as_posix()
            for path in outcome.local_files
        ],
        "changed_files": [
            path.relative_to(outcome.project_root).as_posix()
            for path in outcome.changed_files
        ],
    }
    if explain_local_paths:
        data["local_paths"] = {
            "project_root": str(outcome.project_root),
            "stores": {
                name: str(store.root)
                for name, store in outcome.projection.stores.items()
            },
            "files": [str(path) for path in outcome.local_files],
        }
    return data


def _configure_warnings(outcome: ConfigureOutcome) -> list[dict[str, Any]]:
    if not outcome.missing_entry_pages:
        return []
    return [
        {
            "code": "missing_entry_pages",
            "message": "The local projection is usable, but declared entry pages are missing.",
            "paths": [str(path) for path in outcome.missing_entry_pages],
            "correction": "Restore the missing pages in the project store or update the shared manifest through review.",
        }
    ]


def _render_configure_human(outcome: ConfigureOutcome, *, explain_local_paths: bool) -> None:
    status = "degraded" if outcome.missing_entry_pages else "ok"
    print(f"[{status}] projection     .agents/memory.local.json")
    print(f"[ok] principal      {outcome.projection.principal_role.value}")
    print("[ok] local files    ignored by Git")
    if outcome.missing_entry_pages:
        print(f"[degraded] pages    {len(outcome.missing_entry_pages)} declared page(s) missing")
        for path in outcome.missing_entry_pages:
            print(f"  - {path}")
    if explain_local_paths:
        print(f"[local] project     {outcome.project_root}")
        for name, store in outcome.projection.stores.items():
            print(f"[local] {name:<11} {store.root}")


def _render_projection_error_human(error: ProjectionError | ManifestError) -> None:
    print(f"[blocked] configure · {error.code}")
    print(f"Field: {error.field}")
    print(error.message)
    print(f"Correction: {error.correction}")


def _run_manifest(*, json_output: bool) -> int:
    try:
        manifest = load_nearest_manifest()
    except ManifestError as error:
        if json_output:
            _render_json(
                _envelope(
                    command="manifest",
                    status="blocked",
                    project_id=None,
                    data={},
                    errors=[error.as_dict()],
                )
            )
        else:
            _render_error_human(error)
        return error.exit_code

    if json_output:
        _render_json(
            _envelope(
                command="manifest",
                status="ready",
                project_id=manifest.project.id,
                data=_manifest_data(manifest),
            )
        )
    else:
        _render_manifest_human(manifest)
    return 0


def _run_configure(
    *,
    stores: list[str],
    role: str,
    replace_managed: bool,
    explain_local_paths: bool,
    json_output: bool,
) -> int:
    project_id: str | None = None
    try:
        manifest_path = discover_manifest()
        manifest = load_manifest(manifest_path)
        project_id = manifest.project.id
        outcome = configure_projection(
            manifest=manifest,
            manifest_path=manifest_path,
            store_assignments=stores,
            principal_role=PrincipalRole(role),
            replace_managed=replace_managed,
        )
    except (ManifestError, ProjectionError) as error:
        if json_output:
            _render_json(
                _envelope(
                    command="configure",
                    status="blocked",
                    project_id=project_id,
                    data={},
                    errors=[error.as_dict()],
                )
            )
        else:
            _render_projection_error_human(error)
        return error.exit_code

    warnings = _configure_warnings(outcome)
    if json_output:
        _render_json(
            _envelope(
                command="configure",
                status=outcome.status,
                project_id=manifest.project.id,
                data=_configure_data(outcome, explain_local_paths=explain_local_paths),
                warnings=warnings,
            )
        )
    else:
        _render_configure_human(outcome, explain_local_paths=explain_local_paths)
    return outcome.exit_code


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    if arguments.command == "manifest":
        return _run_manifest(json_output=arguments.json_output)
    if arguments.command == "configure":
        return _run_configure(
            stores=arguments.stores,
            role=arguments.role,
            replace_managed=arguments.replace_managed,
            explain_local_paths=arguments.explain_local_paths,
            json_output=arguments.json_output,
        )
    parser.print_help()
    return 0
