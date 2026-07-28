"""Safe, opt-in selection of current repository contracts."""

from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .contracts import CONTRACT_FILE_EXTENSIONS, RepositorySourceConfig


DENIED_DIRECTORY_NAMES = {
    ".agents",
    ".claude",
    ".codex",
    ".gemini",
    ".git",
    ".next",
    ".nuxt",
    ".output",
    ".opencode",
    ".pytest_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "logs",
    "node_modules",
    "out",
    "target",
    "vendor",
    "venv",
}
DENIED_NAME_FRAGMENTS = ("credential", "secret")


@dataclass(frozen=True, slots=True)
class RejectedContractPath:
    path: PurePosixPath
    code: str


@dataclass(frozen=True, slots=True)
class RepositoryContractSelection:
    allowed: tuple[PurePosixPath, ...]
    rejected: tuple[RejectedContractPath, ...]


def _matches(path: str, pattern: str) -> bool:
    variants = {pattern}
    candidate = pattern
    while "**/" in candidate:
        candidate = candidate.replace("**/", "", 1)
        variants.add(candidate)
    return any(fnmatch.fnmatchcase(path, candidate) for candidate in variants)


def _immutable_denial(relative_path: PurePosixPath) -> bool:
    lowered_parts = tuple(part.lower() for part in relative_path.parts)
    name = lowered_parts[-1]
    return (
        any(part in DENIED_DIRECTORY_NAMES for part in lowered_parts[:-1])
        or name == ".env"
        or name.startswith(".env.")
        or name.endswith(".log")
        or any(fragment in name for fragment in DENIED_NAME_FRAGMENTS)
    )


def _candidate_paths(repository_root: Path) -> tuple[Path, ...]:
    candidates: list[Path] = []
    for current_root, directory_names, file_names in os.walk(repository_root, followlinks=False):
        current = Path(current_root)
        relative_root = current.relative_to(repository_root)
        directory_names[:] = sorted(directory_names)
        for directory_name in tuple(directory_names):
            path = current / directory_name
            if path.is_symlink() or directory_name.lower() in DENIED_DIRECTORY_NAMES:
                candidates.append(path)
                directory_names.remove(directory_name)
        candidates.extend(current / name for name in sorted(file_names))
    return tuple(candidates)


def select_repository_contracts(
    source: RepositorySourceConfig,
    *,
    repository_root: Path,
) -> RepositoryContractSelection:
    """Resolve allowlisted files while enforcing immutable V1 safety boundaries."""

    resolved_root = repository_root.resolve(strict=True)
    allowed: list[PurePosixPath] = []
    rejected: list[RejectedContractPath] = []
    for candidate in _candidate_paths(resolved_root):
        relative = PurePosixPath(candidate.relative_to(resolved_root).as_posix())
        relative_text = relative.as_posix()
        if not any(_matches(relative_text, pattern) for pattern in source.include):
            continue
        if any(_matches(relative_text, pattern) for pattern in source.exclude):
            rejected.append(RejectedContractPath(relative, "manifest_exclude"))
            continue
        if _immutable_denial(relative) or (
            candidate.is_dir() and relative.name.lower() in DENIED_DIRECTORY_NAMES
        ):
            rejected.append(RejectedContractPath(relative, "immutable_denylist"))
            continue
        try:
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(resolved_root)
        except (OSError, RuntimeError, ValueError):
            rejected.append(RejectedContractPath(relative, "repository_symlink_escape"))
            continue
        if candidate.is_symlink():
            rejected.append(RejectedContractPath(relative, "repository_symlink_forbidden"))
            continue
        if candidate.is_dir() or not resolved.is_file():
            continue
        if relative.suffix.lower() not in CONTRACT_FILE_EXTENSIONS:
            rejected.append(RejectedContractPath(relative, "contract_extension_forbidden"))
            continue
        allowed.append(relative)
    return RepositoryContractSelection(
        allowed=tuple(sorted(set(allowed), key=PurePosixPath.as_posix)),
        rejected=tuple(sorted(rejected, key=lambda item: item.path.as_posix())),
    )
