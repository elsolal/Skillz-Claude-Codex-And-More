"""Argument parsing and rendering for the portable memory CLI."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from typing import Any

from . import __version__
from .contracts import PUBLIC_SCHEMA_VERSION, MemoryManifest
from .manifest import ManifestError, load_nearest_manifest


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


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    if arguments.command == "manifest":
        return _run_manifest(json_output=arguments.json_output)
    parser.print_help()
    return 0
