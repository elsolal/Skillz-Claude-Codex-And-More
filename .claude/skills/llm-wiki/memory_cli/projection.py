"""Local projection, managed pointers, and Git exclude integration."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, NoReturn

from .contracts import LocalStoreConfig, MemoryManifest, MemoryProjection, PrincipalRole


MANAGED_MARKER = "<!-- Managed by skillz-memory. Local-only; do not commit. -->"
LOCAL_FILE_MODE = 0o600
GIT_EXCLUDE_HEADER = "# Local skillz-memory files (machine-specific, not shared)"


class ProjectionError(Exception):
    """A stable, user-correctable local projection failure."""

    exit_code = 30

    def __init__(self, *, code: str, field: str, message: str, correction: str) -> None:
        super().__init__(message)
        self.code = code
        self.field = field
        self.message = message
        self.correction = correction

    def as_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "field": self.field,
            "message": self.message,
            "correction": self.correction,
        }


def _error(*, code: str, field: str, message: str, correction: str) -> NoReturn:
    raise ProjectionError(code=code, field=field, message=message, correction=correction)


@dataclass(frozen=True, slots=True)
class ConfigureOutcome:
    projection: MemoryProjection
    project_root: Path
    local_files: tuple[Path, ...]
    changed_files: tuple[Path, ...]
    missing_entry_pages: tuple[PurePosixPath, ...]

    @property
    def status(self) -> str:
        return "degraded" if self.missing_entry_pages else "ready"

    @property
    def exit_code(self) -> int:
        return 10 if self.missing_entry_pages else 0


def parse_store_arguments(values: list[str]) -> dict[str, Path]:
    """Parse repeated NAME=ABSOLUTE_PATH store assignments for projection V1."""

    stores: dict[str, Path] = {}
    for index, value in enumerate(values):
        name, separator, raw_path = value.partition("=")
        field = f"store.{index}"
        if not separator or not name or not raw_path:
            _error(
                code="invalid_store_assignment",
                field=field,
                message="A store assignment is not in the required NAME=PATH form.",
                correction='Use an assignment such as --store project="/absolute/path/to/vault".',
            )
        if name != "project":
            _error(
                code="unknown_store",
                field=field,
                message="The requested store is not configurable in projection V1.",
                correction='Use exactly one "project=..." store assignment.',
            )
        if name in stores:
            _error(
                code="duplicate_store",
                field=field,
                message=f'Store "{name}" is configured more than once.',
                correction=f'Keep a single --store "{name}=..." assignment.',
            )
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            _error(
                code="local_root_not_absolute",
                field=field,
                message=f'Local root for store "{name}" must be absolute.',
                correction=f'Use --store "{name}=/absolute/path/to/vault".',
            )
        try:
            resolved = path.resolve(strict=True)
        except OSError:
            _error(
                code="local_root_unavailable",
                field=field,
                message=f'Local root for store "{name}" does not exist or cannot be resolved.',
                correction=(
                    "Create or clone the local vault, then pass its absolute directory path."
                ),
            )
        if not resolved.is_dir() or not os.access(resolved, os.R_OK | os.X_OK):
            _error(
                code="local_root_unavailable",
                field=field,
                message=f'Local root for store "{name}" is not an accessible directory.',
                correction=(
                    "Grant the current user read and traversal access to the vault directory."
                ),
            )
        stores[name] = resolved

    if "project" not in stores:
        _error(
            code="missing_store",
            field="store.project",
            message='Required local store "project" was not configured.',
            correction='Pass --store "project=/absolute/path/to/vault".',
        )
    return stores


def _run_git(project_root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(project_root), *arguments],
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        _error(
            code="git_metadata_unavailable",
            field="git",
            message="Git metadata required for local exclusions could not be resolved.",
            correction=(
                "Run memory configure inside a valid Git worktree and verify that Git is installed."
            ),
        )
    return result.stdout.strip()


def _git_paths(project_root: Path) -> tuple[Path, Path]:
    git_root = Path(_run_git(project_root, "rev-parse", "--show-toplevel")).resolve()
    raw_exclude_path = Path(_run_git(project_root, "rev-parse", "--git-path", "info/exclude"))
    exclude_path = (
        raw_exclude_path
        if raw_exclude_path.is_absolute()
        else project_root / raw_exclude_path
    ).resolve()
    return git_root, exclude_path


def _relative_git_patterns(git_root: Path, paths: tuple[Path, ...]) -> tuple[str, ...]:
    patterns: list[str] = []
    for path in paths:
        try:
            relative_path = path.resolve().relative_to(git_root)
        except ValueError:
            _error(
                code="projection_outside_git_root",
                field="projection.local_files",
                message="A generated local file would live outside the current Git worktree.",
                correction="Place .agents/memory.yaml inside the current Git worktree.",
            )
        patterns.append(relative_path.as_posix())
    return tuple(patterns)


def _projection_payload(projection: MemoryProjection) -> dict[str, Any]:
    return {
        "schema_version": projection.schema_version,
        "principal": {"role": projection.principal_role.value},
        "stores": {
            name: {"root": str(store.root)}
            for name, store in projection.stores.items()
        },
    }


def projection_paths(manifest_path: Path) -> tuple[Path, Path, Path, Path]:
    """Return the project root and the three managed local projection paths."""

    project_root = manifest_path.parent.parent.resolve()
    return (
        project_root,
        project_root / ".agents" / "memory.local.json",
        project_root / ".claude" / "project-memory.md",
        project_root / ".agents" / "project-memory.md",
    )


def load_projection(manifest_path: Path) -> MemoryProjection:
    """Read the generated local projection without mutating or leaking local paths."""

    _, projection_path, _, _ = projection_paths(manifest_path)
    try:
        raw = projection_path.read_text(encoding="utf-8")
    except OSError:
        _error(
            code="projection_unavailable",
            field=".agents/memory.local.json",
            message="The local memory projection is missing or cannot be read safely.",
            correction="Run memory configure with the local project store, then retry.",
        )

    def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate projection key")
            result[key] = value
        return result

    def reject_constant(_: str) -> NoReturn:
        raise ValueError("non-standard projection constant")

    try:
        payload = json.loads(
            raw,
            object_pairs_hook=strict_object,
            parse_constant=reject_constant,
        )
    except (json.JSONDecodeError, ValueError):
        _error(
            code="projection_invalid",
            field=".agents/memory.local.json",
            message="The local memory projection is not valid JSON.",
            correction="Run memory configure again to regenerate the managed projection.",
        )
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "principal", "stores"}:
        _error(
            code="projection_invalid",
            field=".agents/memory.local.json",
            message="The local memory projection does not match schema V1.",
            correction="Run memory configure again to regenerate the managed projection.",
        )
    if payload["schema_version"] != 1:
        _error(
            code="projection_invalid",
            field="schema_version",
            message="The local memory projection uses an unsupported schema version.",
            correction="Run memory configure again with the current skillz-memory CLI.",
        )
    principal = payload["principal"]
    stores = payload["stores"]
    if (
        not isinstance(principal, dict)
        or set(principal) != {"role"}
        or principal["role"] not in {role.value for role in PrincipalRole}
        or not isinstance(stores, dict)
        or set(stores) != {"project"}
        or not isinstance(stores["project"], dict)
        or set(stores["project"]) != {"root"}
        or not isinstance(stores["project"]["root"], str)
    ):
        _error(
            code="projection_invalid",
            field=".agents/memory.local.json",
            message="The local memory projection contains invalid principal or store data.",
            correction="Run memory configure again to regenerate the managed projection.",
        )
    root = Path(stores["project"]["root"])
    if not root.is_absolute():
        _error(
            code="projection_invalid",
            field="stores.project.root",
            message="The configured local store root is not absolute.",
            correction="Run memory configure again with an absolute project store path.",
        )
    try:
        resolved_root = root.resolve(strict=True)
    except (OSError, RuntimeError):
        _error(
            code="store_access_denied",
            field="stores.project.root",
            message="The configured local store is missing or cannot be resolved.",
            correction="Restore access to the configured vault or run memory configure again.",
        )
    if not resolved_root.is_dir() or not os.access(resolved_root, os.R_OK | os.X_OK):
        _error(
            code="store_access_denied",
            field="stores.project.root",
            message="The configured local store is not readable by the current user.",
            correction="Restore read and traversal access to the configured vault.",
        )
    return MemoryProjection.create(
        principal_role=PrincipalRole(principal["role"]),
        stores={"project": LocalStoreConfig(root=resolved_root)},
    )


def _render_claude_pointer(
    manifest: MemoryManifest,
    projection: MemoryProjection,
    project_root: Path,
) -> str:
    store = projection.stores["project"]
    pages = "\n".join(f"  - `{page}`" for page in manifest.stores.project.entry_pages)
    return f"""{MANAGED_MARKER}
# Project Memory - {manifest.project.name}

- Project name: {manifest.project.name}
- Project id: `{manifest.project.id}`
- Project path: `{project_root}`
- Long-term memory vault: `{store.root}`
- Memory repo: `{manifest.stores.project.remote}`
- QMD collection: `{manifest.stores.project.collection}`
- Principal role: `{projection.principal_role.value}`
- Start pages:
{pages}

Before non-trivial work:
1. Read this file.
2. Read the relevant wiki index, synthesis, and entity pages.
3. Use QMD if those pages are insufficient.
4. Re-check the live project repo before acting; memory is historical context, not immediate truth.

The local principal role never grants filesystem, Git, or remote access.
Shared policy and actual permissions remain authoritative.

Git rule: this file is machine-specific and must stay ignored by Git.
"""


def _render_agents_pointer(manifest: MemoryManifest, projection: MemoryProjection) -> str:
    store = projection.stores["project"]
    return f"""{MANAGED_MARKER}
# Project Memory - {manifest.project.name}

Read `.claude/project-memory.md` for the canonical local memory pointer.

Memory vault: `{store.root}`
QMD collection: `{manifest.stores.project.collection}`
Memory repo: `{manifest.stores.project.remote}`
Principal role: `{projection.principal_role.value}`

The local principal role never grants filesystem, Git, or remote access.

Git rule: this file is machine-specific and must stay ignored by Git.
"""


def _missing_entry_pages(manifest: MemoryManifest, root: Path) -> tuple[PurePosixPath, ...]:
    missing: list[PurePosixPath] = []
    for entry_page in manifest.stores.project.entry_pages:
        candidate = root.joinpath(*entry_page.parts)
        resolved = candidate.resolve(strict=False)
        try:
            resolved.relative_to(root)
        except ValueError:
            _error(
                code="entry_page_outside_store",
                field=f"stores.project.entry_pages.{entry_page}",
                message=f'Entry page "{entry_page}" resolves outside its local store root.',
                correction=(
                    "Remove the escaping symlink or point the store at the correct vault root."
                ),
            )
        if not resolved.is_file():
            missing.append(entry_page)
    return tuple(missing)


def _preflight_pointer(path: Path, desired: str, *, replace_managed: bool) -> None:
    if not path.exists():
        return
    try:
        current = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        _error(
            code="pointer_unreadable",
            field=path.name,
            message="An existing project-memory pointer cannot be read safely.",
            correction="Fix its permissions or move it aside, then retry.",
        )
    if current == desired or MANAGED_MARKER in current:
        return
    if replace_managed:
        return
    _error(
        code="unmanaged_pointer",
        field=path.relative_to(path.parents[1]).as_posix(),
        message="An existing project-memory pointer is not managed by skillz-memory.",
        correction=(
            "Preserve or move the custom file, or retry with --replace-managed "
            "to replace it explicitly."
        ),
    )


def _atomic_write(path: Path, content: str, *, mode: int | None) -> bool:
    encoded = content.encode("utf-8")
    if path.exists():
        try:
            if path.read_bytes() == encoded:
                if mode is not None:
                    try:
                        os.chmod(path, mode)
                    except OSError:
                        _error(
                            code="local_write_failed",
                            field=path.name,
                            message="Local file permissions could not be restricted.",
                            correction="Grant ownership of the local file to the current user.",
                        )
                return False
        except OSError:
            _error(
                code="local_file_unreadable",
                field=path.name,
                message="A local managed file cannot be read safely.",
                correction="Fix its permissions or move it aside, then retry.",
            )

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        existing_mode = path.stat().st_mode & 0o777 if path.exists() else None
    except OSError:
        _error(
            code="local_write_failed",
            field=path.name,
            message="The local managed file directory cannot be prepared safely.",
            correction="Check directory permissions and available disk space, then retry.",
        )
    target_mode = mode if mode is not None else (existing_mode or 0o644)
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.",
            dir=path.parent,
        )
    except OSError:
        _error(
            code="local_write_failed",
            field=path.name,
            message="A local atomic write could not be started safely.",
            correction="Check directory permissions and available disk space, then retry.",
        )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as temporary_file:
            temporary_file.write(encoded)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.chmod(temporary_path, target_mode)
        os.replace(temporary_path, path)
    except OSError:
        try:
            temporary_path.unlink(missing_ok=True)
        except OSError:
            pass
        _error(
            code="local_write_failed",
            field=path.name,
            message="A local managed file could not be written atomically.",
            correction="Check directory permissions and available disk space, then retry.",
        )
    return True


def _ensure_git_excludes(exclude_path: Path, patterns: tuple[str, ...]) -> bool:
    try:
        current = exclude_path.read_text(encoding="utf-8") if exclude_path.exists() else ""
    except (OSError, UnicodeError):
        _error(
            code="git_exclude_unreadable",
            field="git.info.exclude",
            message="Git exclude rules cannot be read safely.",
            correction="Fix the repository's info/exclude permissions, then retry.",
        )
    existing_lines = set(current.splitlines())
    missing_patterns = [pattern for pattern in patterns if pattern not in existing_lines]
    if not missing_patterns:
        return False

    suffix_lines: list[str] = []
    if current and not current.endswith("\n"):
        suffix_lines.append("")
    if GIT_EXCLUDE_HEADER not in existing_lines:
        if current and current.strip():
            suffix_lines.append("")
        suffix_lines.append(GIT_EXCLUDE_HEADER)
    suffix_lines.extend(missing_patterns)
    new_content = current + "\n".join(suffix_lines) + "\n"
    return _atomic_write(exclude_path, new_content, mode=None)


def configure_projection(
    *,
    manifest: MemoryManifest,
    manifest_path: Path,
    store_assignments: list[str],
    principal_role: PrincipalRole,
    replace_managed: bool,
) -> ConfigureOutcome:
    """Validate and write the local projection as one preflighted operation."""

    store_roots = parse_store_arguments(store_assignments)
    project_root, projection_path, claude_pointer, agents_pointer = projection_paths(
        manifest_path
    )
    projection = MemoryProjection.create(
        principal_role=principal_role,
        stores={name: LocalStoreConfig(root=root) for name, root in store_roots.items()},
    )
    local_files = (projection_path, claude_pointer, agents_pointer)

    projection_content = json.dumps(
        _projection_payload(projection),
        ensure_ascii=False,
        indent=2,
    ) + "\n"
    claude_content = _render_claude_pointer(manifest, projection, project_root)
    agents_content = _render_agents_pointer(manifest, projection)
    _preflight_pointer(claude_pointer, claude_content, replace_managed=replace_managed)
    _preflight_pointer(agents_pointer, agents_content, replace_managed=replace_managed)
    missing_pages = _missing_entry_pages(manifest, projection.stores["project"].root)

    git_root, exclude_path = _git_paths(project_root)
    patterns = _relative_git_patterns(git_root, local_files)
    _ensure_git_excludes(exclude_path, patterns)

    changed: list[Path] = []
    for path, content in (
        (projection_path, projection_content),
        (claude_pointer, claude_content),
        (agents_pointer, agents_content),
    ):
        if _atomic_write(path, content, mode=LOCAL_FILE_MODE):
            changed.append(path)

    return ConfigureOutcome(
        projection=projection,
        project_root=project_root,
        local_files=local_files,
        changed_files=tuple(changed),
        missing_entry_pages=missing_pages,
    )
