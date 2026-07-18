"""Local-first activation diagnostics for portable project memory."""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import MemoryManifest
from .manifest import ManifestError, discover_manifest, load_manifest
from .projection import (
    MANAGED_MARKER,
    ProjectionError,
    configure_projection,
    load_projection,
    projection_paths,
)
from .qmd_adapter import QmdInvocationError, QmdOutputError, inspect_qmd


QMD_INSTALL_COMMAND = "bun install -g @tobilu/qmd"
QMD_FRESHNESS_WARNING_SECONDS = 24 * 60 * 60


Runner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True, slots=True)
class DoctorCheck:
    id: str
    status: str
    message: str
    correction: str | None = None

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "id": self.id,
            "status": self.status,
            "message": self.message,
        }
        if self.correction is not None:
            result["correction"] = self.correction
        return result


@dataclass(frozen=True, slots=True)
class DoctorOutcome:
    status: str
    exit_code: int
    project_id: str | None
    project_name: str | None
    checks: tuple[DoctorCheck, ...]
    available_modes: tuple[str, ...]
    unavailable_modes: tuple[str, ...]
    start_question: str | None
    next_actions: tuple[str, ...]
    warnings: tuple[dict[str, Any], ...]
    errors: tuple[dict[str, Any], ...]

    def data(self) -> dict[str, Any]:
        return {
            "summary": {
                "ready": sum(check.status == "ready" for check in self.checks),
                "total": len(self.checks),
            },
            "checks": [check.as_dict() for check in self.checks],
            "capabilities": {
                "available_modes": list(self.available_modes),
                "unavailable_modes": list(self.unavailable_modes),
            },
            "start_question": self.start_question,
            "next_actions": list(self.next_actions),
        }


def _blocked(
    *,
    project_id: str | None,
    project_name: str | None,
    checks: list[DoctorCheck],
    error: dict[str, Any],
    exit_code: int,
    next_action: str,
) -> DoctorOutcome:
    return DoctorOutcome(
        status="blocked",
        exit_code=exit_code,
        project_id=project_id,
        project_name=project_name,
        checks=tuple(checks),
        available_modes=(),
        unavailable_modes=("minimal", "project", "historical"),
        start_question=None,
        next_actions=(next_action,),
        warnings=(),
        errors=(error,),
    )


def _run_git(
    arguments: Sequence[str],
    *,
    runner: Runner,
    timeout_seconds: float,
) -> subprocess.CompletedProcess[str]:
    try:
        return runner(
            list(arguments),
            check=False,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError("Git invocation failed or timed out.") from error


def _check_git_local_files(
    *,
    manifest_path: Path,
    runner: Runner,
    timeout_seconds: float,
) -> tuple[DoctorCheck, dict[str, Any] | None]:
    project_root, _, claude_pointer, agents_pointer = projection_paths(manifest_path)
    local_files = (
        project_root / ".agents" / "memory.local.json",
        claude_pointer,
        agents_pointer,
    )
    for path in (claude_pointer, agents_pointer):
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            return (
                DoctorCheck(
                    id="git_ignore",
                    status="blocked",
                    message="A managed project-memory pointer is missing or unreadable.",
                    correction="Run memory doctor --fix after validating the local projection.",
                ),
                {
                    "code": "managed_pointer_unavailable",
                    "message": "A managed project-memory pointer is missing or unreadable.",
                    "correction": "Run memory doctor --fix after validating the local projection.",
                },
            )
        if MANAGED_MARKER not in content:
            return (
                DoctorCheck(
                    id="git_ignore",
                    status="blocked",
                    message="A project-memory pointer is not managed by skillz-memory.",
                    correction=(
                        "Preserve the custom pointer or replace it explicitly "
                        "with memory configure."
                    ),
                ),
                {
                    "code": "unmanaged_pointer",
                    "message": "A project-memory pointer is not managed by skillz-memory.",
                    "correction": (
                        "Preserve the custom pointer or replace it explicitly "
                        "with memory configure."
                    ),
                },
            )

    for path in local_files:
        relative = path.relative_to(project_root).as_posix()
        tracked = _run_git(
            ["git", "-C", str(project_root), "ls-files", "--error-unmatch", "--", relative],
            runner=runner,
            timeout_seconds=timeout_seconds,
        )
        if tracked.returncode == 0:
            return (
                DoctorCheck(
                    id="git_ignore",
                    status="blocked",
                    message="A machine-local memory file is tracked by Git.",
                    correction=f"Review and untrack {relative}, then run memory doctor again.",
                ),
                {
                    "code": "local_file_tracked",
                    "path": relative,
                    "message": "A machine-local memory file is tracked by Git.",
                    "correction": f"Review and untrack {relative}, then run memory doctor again.",
                },
            )
        if tracked.returncode not in {0, 1}:
            raise RuntimeError("Git could not inspect tracked local files.")
        ignored = _run_git(
            ["git", "-C", str(project_root), "check-ignore", "-q", "--", relative],
            runner=runner,
            timeout_seconds=timeout_seconds,
        )
        if ignored.returncode not in {0, 1}:
            raise RuntimeError("Git could not inspect local ignore rules.")
        if ignored.returncode == 1:
            return (
                DoctorCheck(
                    id="git_ignore",
                    status="blocked",
                    message="A machine-local memory file is not ignored by Git.",
                    correction="Run memory doctor --fix to restore managed local exclusions.",
                ),
                {
                    "code": "local_file_not_ignored",
                    "path": relative,
                    "message": "A machine-local memory file is not ignored by Git.",
                    "correction": "Run memory doctor --fix to restore managed local exclusions.",
                },
            )
    return (
        DoctorCheck(
            id="git_ignore",
            status="ready",
            message="Managed local files are untracked and ignored by Git.",
        ),
        None,
    )


def _check_entry_pages(
    manifest: MemoryManifest,
    store_root: Path,
) -> tuple[DoctorCheck, dict[str, Any] | None]:
    missing: list[str] = []
    for entry_page in manifest.stores.project.entry_pages:
        candidate = store_root.joinpath(*entry_page.parts)
        try:
            resolved = candidate.resolve(strict=False)
            resolved.relative_to(store_root)
        except (OSError, ValueError):
            return (
                DoctorCheck(
                    id="entry_pages",
                    status="blocked",
                    message=(
                        "An entry page escapes or cannot be resolved inside "
                        "the project store."
                    ),
                    correction="Repair the declared entry page or its symlink, then retry.",
                ),
                {
                    "code": "entry_page_access_denied",
                    "message": "An entry page escapes or cannot be resolved inside the project store.",
                    "correction": "Repair the declared entry page or its symlink, then retry.",
                },
            )
        if resolved.exists() and not os.access(resolved, os.R_OK):
            return (
                DoctorCheck(
                    id="entry_pages",
                    status="blocked",
                    message="A required entry page cannot be read by the current user.",
                    correction="Restore read access to the declared entry page, then retry.",
                ),
                {
                    "code": "entry_page_access_denied",
                    "message": "A required entry page cannot be read by the current user.",
                    "correction": "Restore read access to the declared entry page, then retry.",
                },
            )
        if not resolved.is_file():
            missing.append(entry_page.as_posix())
    if missing:
        return (
            DoctorCheck(
                id="entry_pages",
                status="blocked",
                message=f"{len(missing)} required entry page(s) are missing.",
                correction=(
                    "Restore the missing pages or update the shared manifest "
                    "through review."
                ),
            ),
            {
                "code": "missing_entry_pages",
                "paths": missing,
                "message": "Required entry pages are missing from the configured project store.",
                "correction": (
                    "Restore the missing pages or update the shared manifest "
                    "through review."
                ),
            },
        )
    return (
        DoctorCheck(
            id="entry_pages",
            status="ready",
            message=(
                f"{len(manifest.stores.project.entry_pages)} declared entry "
                "page(s) are available."
            ),
        ),
        None,
    )


@dataclass(frozen=True, slots=True)
class QmdDiagnostic:
    checks: tuple[DoctorCheck, DoctorCheck]
    ready: bool
    warnings: tuple[dict[str, Any], ...]
    next_actions: tuple[str, ...]


def _diagnose_qmd(
    manifest: MemoryManifest,
    *,
    runner: Runner,
    timeout_seconds: float,
) -> QmdDiagnostic:
    qmd_override = os.environ.get("SKILLZ_MEMORY_QMD")
    qmd_executable = qmd_override if qmd_override is not None else shutil.which("qmd")
    if qmd_executable is None or not Path(qmd_executable).is_file():
        return QmdDiagnostic(
            checks=(
                DoctorCheck("qmd", "degraded", "QMD is not installed.", QMD_INSTALL_COMMAND),
                DoctorCheck(
                    "freshness",
                    "degraded",
                    "QMD freshness is unavailable while entry pages remain usable.",
                ),
            ),
            ready=False,
            warnings=(
                {
                    "code": "qmd_missing",
                    "message": "QMD is unavailable; bounded entry-page modes remain usable.",
                    "correction": QMD_INSTALL_COMMAND,
                },
            ),
            next_actions=(QMD_INSTALL_COMMAND, "memory doctor"),
        )

    try:
        qmd_status = inspect_qmd(
            qmd_executable,
            runner=runner,
            timeout_seconds=timeout_seconds,
        )
    except (QmdInvocationError, QmdOutputError):
        correction = "Repair or update QMD 0.9.x, then run memory doctor again."
        return QmdDiagnostic(
            checks=(
                DoctorCheck(
                    "qmd",
                    "degraded",
                    "QMD status could not be interpreted safely.",
                    correction,
                ),
                DoctorCheck(
                    "freshness",
                    "degraded",
                    "QMD freshness is unavailable while entry pages remain usable.",
                ),
            ),
            ready=False,
            warnings=(
                {
                    "code": "qmd_status_unavailable",
                    "message": "QMD status could not be interpreted safely.",
                    "correction": correction,
                },
            ),
            next_actions=(correction,),
        )

    collection = qmd_status.collections.get(manifest.stores.project.collection)
    if collection is None:
        correction = (
            f"Configure the {manifest.stores.project.collection} QMD collection, "
            "then run memory doctor."
        )
        return QmdDiagnostic(
            checks=(
                DoctorCheck(
                    "qmd",
                    "degraded",
                    "The declared QMD collection is unknown.",
                    correction,
                ),
                DoctorCheck(
                    "freshness",
                    "degraded",
                    "QMD freshness is unavailable while entry pages remain usable.",
                ),
            ),
            ready=False,
            warnings=(
                {
                    "code": "qmd_collection_unknown",
                    "message": "The declared QMD collection is not present locally.",
                    "correction": correction,
                },
            ),
            next_actions=(correction,),
        )

    qmd_check = DoctorCheck(
        "qmd",
        "ready",
        f"QMD 0.9.x exposes the declared collection with {collection.files} indexed file(s).",
    )
    if collection.age_seconds <= QMD_FRESHNESS_WARNING_SECONDS:
        return QmdDiagnostic(
            checks=(
                qmd_check,
                DoctorCheck("freshness", "ready", "The local QMD collection is fresh."),
            ),
            ready=True,
            warnings=(),
            next_actions=(),
        )

    correction = "qmd update && qmd embed"
    return QmdDiagnostic(
        checks=(
            qmd_check,
            DoctorCheck(
                "freshness",
                "degraded",
                "The local QMD collection is older than 24 hours.",
                correction,
            ),
        ),
        ready=True,
        warnings=(
            {
                "code": "qmd_index_stale",
                "message": "The local QMD collection is older than 24 hours.",
                "correction": correction,
            },
        ),
        next_actions=("qmd update", "qmd embed", "memory doctor"),
    )


def _check_network(
    manifest: MemoryManifest,
    *,
    runner: Runner,
    timeout_seconds: float,
) -> tuple[DoctorCheck, dict[str, Any] | None]:
    try:
        remote = _run_git(
            ["git", "ls-remote", "--exit-code", manifest.stores.project.remote, "HEAD"],
            runner=runner,
            timeout_seconds=max(timeout_seconds, 5.0),
        )
    except RuntimeError:
        remote = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="")
    if remote.returncode == 0:
        return DoctorCheck("network", "ready", "The declared memory remote is reachable."), None
    error = {
        "code": "remote_access_denied",
        "message": "The declared memory remote could not be reached or authorized.",
        "correction": "Verify network access and Git credentials, then retry with --network.",
    }
    return DoctorCheck("network", "blocked", error["message"], error["correction"]), error


def run_doctor(
    *,
    fix: bool = False,
    network: bool = False,
    runner: Runner = subprocess.run,
    timeout_seconds: float = 1.0,
) -> DoctorOutcome:
    checks: list[DoctorCheck] = []
    warnings: list[dict[str, Any]] = []
    next_actions: list[str] = []
    project_id: str | None = None
    project_name: str | None = None

    try:
        manifest_path = discover_manifest()
        manifest = load_manifest(manifest_path)
    except ManifestError as error:
        return _blocked(
            project_id=None,
            project_name=None,
            checks=[DoctorCheck("manifest", "blocked", error.message, error.correction)],
            error=error.as_dict(),
            exit_code=error.exit_code,
            next_action=error.correction,
        )
    project_id = manifest.project.id
    project_name = manifest.project.name
    if manifest.golden.start_question is None:
        checks.append(
            DoctorCheck(
                "manifest",
                "degraded",
                "The manifest is valid but has no golden start question.",
                'Add "golden.start_question" to .agents/memory.yaml through review.',
            )
        )
        warnings.append(
            {
                "code": "start_question_missing",
                "message": "The manifest has no golden start question.",
                "correction": 'Add "golden.start_question" to .agents/memory.yaml through review.',
            }
        )
        next_actions.append('Add "golden.start_question" to .agents/memory.yaml')
    else:
        checks.append(
            DoctorCheck("manifest", "ready", "Manifest schema V1 and start question are valid.")
        )

    try:
        projection = load_projection(manifest_path)
        if fix:
            configure_projection(
                manifest=manifest,
                manifest_path=manifest_path,
                store_assignments=[f"project={projection.stores['project'].root}"],
                principal_role=projection.principal_role,
                replace_managed=False,
            )
            projection = load_projection(manifest_path)
    except ProjectionError as error:
        exit_code = 32 if error.code == "store_access_denied" else error.exit_code
        return _blocked(
            project_id=project_id,
            project_name=project_name,
            checks=checks + [DoctorCheck("projection", "blocked", error.message, error.correction)],
            error=error.as_dict(),
            exit_code=exit_code,
            next_action=error.correction,
        )
    checks.append(
        DoctorCheck("projection", "ready", "The local projection is valid and accessible.")
    )

    try:
        git_check, git_error = _check_git_local_files(
            manifest_path=manifest_path,
            runner=runner,
            timeout_seconds=timeout_seconds,
        )
    except RuntimeError:
        error = {
            "code": "git_unavailable",
            "message": "Git is unavailable for local projection checks.",
            "correction": "Install Git or restore repository access, then retry.",
        }
        return _blocked(
            project_id=project_id,
            project_name=project_name,
            checks=checks
            + [DoctorCheck("git_ignore", "blocked", error["message"], error["correction"])],
            error=error,
            exit_code=31,
            next_action=error["correction"],
        )
    checks.append(git_check)
    if git_error is not None:
        return _blocked(
            project_id=project_id,
            project_name=project_name,
            checks=checks,
            error=git_error,
            exit_code=30,
            next_action=git_error["correction"],
        )

    pages_check, pages_error = _check_entry_pages(
        manifest,
        projection.stores["project"].root,
    )
    checks.append(pages_check)
    if pages_error is not None:
        exit_code = 32 if pages_error["code"] == "entry_page_access_denied" else 30
        return _blocked(
            project_id=project_id,
            project_name=project_name,
            checks=checks,
            error=pages_error,
            exit_code=exit_code,
            next_action=pages_error["correction"],
        )

    qmd = _diagnose_qmd(manifest, runner=runner, timeout_seconds=timeout_seconds)
    checks.extend(qmd.checks)
    warnings.extend(qmd.warnings)
    next_actions.extend(qmd.next_actions)

    if network:
        network_check, network_error = _check_network(
            manifest,
            runner=runner,
            timeout_seconds=timeout_seconds,
        )
        checks.append(network_check)
        if network_error is not None:
            return _blocked(
                project_id=project_id,
                project_name=project_name,
                checks=checks,
                error=network_error,
                exit_code=32,
                next_action=network_error["correction"],
            )

    available_modes = ("minimal", "project", "historical") if qmd.ready else ("minimal", "project")
    unavailable_modes = () if qmd.ready else ("historical",)
    status = "degraded" if warnings else "ready"
    return DoctorOutcome(
        status=status,
        exit_code=10 if status == "degraded" else 0,
        project_id=project_id,
        project_name=project_name,
        checks=tuple(checks),
        available_modes=available_modes,
        unavailable_modes=unavailable_modes,
        start_question=manifest.golden.start_question,
        next_actions=tuple(dict.fromkeys(next_actions)),
        warnings=tuple(warnings),
        errors=(),
    )
