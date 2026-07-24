"""Argument parsing and rendering for the portable memory CLI."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import replace
from typing import Any

from . import __version__
from .context import run_context
from .contracts import (
    PUBLIC_SCHEMA_VERSION,
    ImpactCode,
    MemoryManifest,
    PrincipalRole,
    RetrievalMode,
    RiskReason,
    TaskCategory,
)
from .doctor import DoctorOutcome, run_doctor
from .events import (
    EventIntegrityError,
    append_event,
    append_usage_attestation,
    build_context_event,
    purge_project_events,
    resolve_state_dir,
)
from .manifest import ManifestError, discover_manifest, load_manifest, load_nearest_manifest
from .projection import ConfigureOutcome, ProjectionError, configure_projection
from .receipts import FinishOutcome
from .render_human import render_context_final, render_context_initial, render_finish_human
from .render_json import render_context_json, render_finish_json


MAX_QUERY_CHARACTERS = 16 * 1024


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
        help=(
            "Map a logical store to an absolute local root "
            "(project is required; declared fallback IDs are optional)."
        ),
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
    doctor_parser = commands.add_parser(
        "doctor",
        help="Diagnose local memory activation without mutating it by default.",
    )
    doctor_parser.add_argument(
        "--network",
        action="store_true",
        help="Explicitly verify access to the declared memory remote without fetching.",
    )
    doctor_parser.add_argument(
        "--fix",
        action="store_true",
        help="Repair only managed local projection files and Git exclusions.",
    )
    doctor_parser.add_argument(
        "--explain",
        action="store_true",
        help="Show detailed check explanations and available capabilities.",
    )
    doctor_parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit the stable machine-readable result envelope.",
    )
    context_parser = commands.add_parser(
        "context",
        help="Retrieve the first bounded project-memory route for a task.",
    )
    context_parser.add_argument(
        "query",
        nargs="?",
        help="Task query; use --query-stdin for sensitive input.",
    )
    context_parser.add_argument(
        "--query-stdin",
        action="store_true",
        help="Read the query from stdin without persisting it in memory artifacts.",
    )
    context_parser.add_argument(
        "--mode",
        choices=[mode.value for mode in RetrievalMode],
        default=RetrievalMode.PROJECT.value,
        help="Retrieval envelope to prepare (default: project).",
    )
    context_parser.add_argument(
        "--task-category",
        choices=[category.value for category in TaskCategory],
        required=True,
        help="Classify the task for deterministic routing and later sufficiency decisions.",
    )
    context_parser.add_argument(
        "--fallback-on-ambiguous",
        action="store_true",
        help="Explicitly allow an authorized fallback when project evidence is ambiguous.",
    )
    context_parser.add_argument(
        "--risk-reason",
        choices=[reason.value for reason in RiskReason],
        help="Authorize a necessary hard-cap overrun with an auditable risk category.",
    )
    context_parser.add_argument(
        "--explain",
        action="store_true",
        help="Show sufficiency evidence, reason codes and fallback decisions.",
    )
    context_parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit the stable machine-readable result envelope.",
    )
    finish_parser = commands.add_parser(
        "finish",
        help="Append usage, citations and impact attested for a context event.",
    )
    finish_parser.add_argument(
        "parent_event_id",
        help="The event_id returned by memory context.",
    )
    finish_parser.add_argument(
        "--used",
        action="append",
        default=[],
        metavar="DOCID",
        help="Declare a retrieved docid that influenced the work; repeat as needed.",
    )
    finish_parser.add_argument(
        "--cited",
        action="append",
        default=[],
        metavar="DOCID",
        help="Declare a retrieved docid cited in the final output; repeat as needed.",
    )
    finish_parser.add_argument(
        "--citation-only",
        action="append",
        default=[],
        metavar="DOCID",
        help="Justify a cited docid that did not influence the work; repeat as needed.",
    )
    finish_parser.add_argument(
        "--impact-code",
        action="append",
        default=[],
        choices=[code.value for code in ImpactCode],
        help="Attest one impact-v1 outcome; repeat as needed.",
    )
    finish_parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit the stable machine-readable result envelope.",
    )
    purge_parser = commands.add_parser(
        "purge",
        help="Apply retention or remove current-project memory event detail.",
    )
    purge_parser.add_argument(
        "--force",
        action="store_true",
        help="Immediately remove all event detail for the current project.",
    )
    purge_parser.add_argument(
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
            "sufficiency_thresholds_version": (
                manifest.policy.sufficiency_thresholds_version
            ),
        },
        "golden": {
            "visible_path": str(manifest.golden.visible_path),
            "quality_rubric": str(manifest.golden.quality_rubric),
            **(
                {"start_question": manifest.golden.start_question}
                if manifest.golden.start_question is not None
                else {}
            ),
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


def _render_doctor_human(outcome: DoctorOutcome, *, explain: bool) -> None:
    project_name = outcome.project_name or "Unknown project"
    print(f"Memory Doctor · {project_name}")
    ready_count = sum(check.status == "ready" for check in outcome.checks)
    print(
        f"Status: {outcome.status.upper()} · "
        f"{ready_count}/{len(outcome.checks)} checks ready"
    )
    print()
    labels = {"ready": "ok", "degraded": "!!", "blocked": "xx"}
    for check in outcome.checks:
        print(f"[{labels.get(check.status, '--')}] {check.id:<13} {check.message}")
        if explain and check.correction:
            print(f"    Correction: {check.correction}")
    if outcome.start_question is not None:
        print()
        print("Start question")
        print(f"  {outcome.start_question}")
    if explain:
        print()
        print(f"Available modes: {', '.join(outcome.available_modes) or 'none'}")
        if outcome.unavailable_modes:
            print(f"Unavailable modes: {', '.join(outcome.unavailable_modes)}")
    if outcome.next_actions:
        print()
        print("Next action" if len(outcome.next_actions) == 1 else "Next actions")
        for action in outcome.next_actions:
            print(f"  {action}")
    if not explain and outcome.status != "ready":
        print()
        print("Details: memory doctor --explain")
    print("Machine output: memory doctor --json")


def _run_doctor_command(
    *,
    network: bool,
    fix: bool,
    explain: bool,
    json_output: bool,
) -> int:
    outcome = run_doctor(network=network, fix=fix)
    if json_output:
        _render_json(
            _envelope(
                command="doctor",
                status=outcome.status,
                project_id=outcome.project_id,
                data=outcome.data(),
                warnings=list(outcome.warnings),
                errors=list(outcome.errors),
            )
        )
    else:
        _render_doctor_human(outcome, explain=explain)
    return outcome.exit_code


def _run_context_command(
    *,
    mode: str,
    task_category: str,
    query: str,
    fallback_on_ambiguous: bool,
    risk_reason: str | None,
    explain: bool,
    json_output: bool,
) -> int:
    try:
        manifest_path = discover_manifest()
        outcome = run_context(
            mode=RetrievalMode(mode),
            task_category=TaskCategory(task_category),
            query=query,
            fallback_on_ambiguous=fallback_on_ambiguous,
            risk_reason=RiskReason(risk_reason) if risk_reason else None,
            on_initial_receipt=lambda receipt: render_context_initial(
                receipt,
                stream=sys.stderr,
            ),
        )
    except (ManifestError, ProjectionError) as error:
        if json_output:
            _render_json(
                _envelope(
                    command="context",
                    status="blocked",
                    project_id=None,
                    data={},
                    errors=[error.as_dict()],
                )
            )
        else:
            print(f"[blocked] memory context · {error.code}")
            print(error.message)
            print(f"Correction: {error.correction}")
        return error.exit_code

    try:
        event = build_context_event(outcome.event_metadata())
        append_event(
            event,
            state_dir=resolve_state_dir(),
            project_root=manifest_path.parent.parent,
        )
        outcome = replace(outcome, event_id=str(event["event_id"]))
    except EventIntegrityError as error:
        outcome = replace(
            outcome,
            exit_code=error.exit_code,
            errors=(*outcome.errors, error.as_dict()),
        )

    if json_output:
        render_context_json(outcome, stream=sys.stdout)
    else:
        render_context_final(outcome, explain=explain, stream=sys.stdout)
    return outcome.exit_code


def _run_purge_command(*, force: bool, json_output: bool) -> int:
    project_id: str | None = None
    try:
        manifest_path = discover_manifest()
        manifest = load_manifest(manifest_path)
        project_id = manifest.project.id
        outcome = purge_project_events(
            project_id,
            retention_days=manifest.policy.retention_days,
            force=force,
            state_dir=resolve_state_dir(),
            project_root=manifest_path.parent.parent,
        )
    except (ManifestError, EventIntegrityError) as error:
        if json_output:
            _render_json(
                _envelope(
                    command="purge",
                    status="blocked",
                    project_id=project_id,
                    data={},
                    errors=[error.as_dict()],
                )
            )
        else:
            print(f"[blocked] memory purge · {error.code}")
            print(error.message)
            print(f"Correction: {error.correction}")
        return error.exit_code

    if json_output:
        _render_json(
            _envelope(
                command="purge",
                status="ready",
                project_id=project_id,
                data=outcome.data(),
            )
        )
    else:
        mode = "forced" if force else "retention"
        print(f"Memory purge · {project_id} · {mode}")
        print(f"Deleted: {outcome.deleted_events} event(s)")
        print(f"Retained: {outcome.retained_events} event(s)")
        if outcome.corrupted_files:
            print(
                "Warning: "
                f"{outcome.corrupted_files} truncated file(s) were rewritten from their valid prefix."
            )
    return 0


def _run_finish_command(
    *,
    parent_event_id: str,
    used: Sequence[str],
    cited: Sequence[str],
    citation_only: Sequence[str],
    impact_codes: Sequence[str],
    json_output: bool,
) -> int:
    project_id: str | None = None
    try:
        manifest_path = discover_manifest()
        manifest = load_manifest(manifest_path)
        project_id = manifest.project.id
        result = append_usage_attestation(
            project_id=project_id,
            parent_event_id=parent_event_id,
            used=used,
            cited=cited,
            citation_only=citation_only,
            impact_codes=impact_codes,
            state_dir=resolve_state_dir(),
            project_root=manifest_path.parent.parent,
        )
    except (ManifestError, EventIntegrityError) as error:
        if json_output:
            _render_json(
                _envelope(
                    command="finish",
                    status="blocked",
                    project_id=project_id,
                    data={"parent_event_id": parent_event_id},
                    errors=[error.as_dict()],
                )
            )
        else:
            print(f"[blocked] memory finish · {error.code}")
            print(error.message)
            print(f"Correction: {error.correction}")
        return error.exit_code

    outcome = FinishOutcome(
        project_id=project_id,
        parent_event=result.parent_event,
        attestation_event=result.event,
    )
    if json_output:
        render_finish_json(outcome, stream=sys.stdout)
    else:
        render_finish_human(outcome, stream=sys.stdout)
    return 0


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
    if arguments.command == "doctor":
        return _run_doctor_command(
            network=arguments.network,
            fix=arguments.fix,
            explain=arguments.explain,
            json_output=arguments.json_output,
        )
    if arguments.command == "finish":
        return _run_finish_command(
            parent_event_id=arguments.parent_event_id,
            used=arguments.used,
            cited=arguments.cited,
            citation_only=arguments.citation_only,
            impact_codes=arguments.impact_code,
            json_output=arguments.json_output,
        )
    if arguments.command == "purge":
        return _run_purge_command(
            force=arguments.force,
            json_output=arguments.json_output,
        )
    if arguments.command == "context":
        if arguments.query_stdin and arguments.query is not None:
            parser.error("context accepts either a query argument or --query-stdin, not both")
        if arguments.query_stdin:
            query = sys.stdin.read(MAX_QUERY_CHARACTERS + 1)
            if len(query) > MAX_QUERY_CHARACTERS:
                parser.error(
                    f"context query must not exceed {MAX_QUERY_CHARACTERS} characters"
                )
        elif arguments.query is not None:
            query = arguments.query
        else:
            parser.error("context requires a query argument or --query-stdin")
        if not query.strip():
            parser.error("context query must not be empty")
        return _run_context_command(
            mode=arguments.mode,
            task_category=arguments.task_category,
            query=query,
            fallback_on_ambiguous=arguments.fallback_on_ambiguous,
            risk_reason=arguments.risk_reason,
            explain=arguments.explain,
            json_output=arguments.json_output,
        )
    parser.print_help()
    return 0
