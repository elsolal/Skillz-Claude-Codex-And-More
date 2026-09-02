#!/usr/bin/env python3
"""Capture a deterministic inventory of Skillz-owned distribution surfaces."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
from typing import Any, Iterable


SCHEMA_VERSION = 1
BASELINE_ID = "legacy-v6"
GENERATOR = "scripts/capture_distribution_baseline.py"
INCLUDED_PREFIXES = (
    ".claude/",
    ".claude-plugin/",
    ".codex/",
    ".gemini/",
    ".opencode/",
    "scripts/",
)
INCLUDED_FILES = {
    "AGENTS.md",
    "GEMINI.md",
    "README.md",
    "commands",
    "install.sh",
    "skills",
}
EXCLUDED_FILES = {GENERATOR}


class BaselineError(RuntimeError):
    """Raised when the repository cannot be inventoried safely."""


def _git_tracked_paths(root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        message = completed.stderr.decode("utf-8", errors="replace").strip()
        raise BaselineError(f"git ls-files failed: {message or 'unknown error'}")
    paths = completed.stdout.decode("utf-8", errors="surrogateescape").split("\0")
    return sorted(path for path in paths if path)


def _is_distribution_path(relative_path: str) -> bool:
    if relative_path in EXCLUDED_FILES:
        return False
    return relative_path in INCLUDED_FILES or relative_path.startswith(INCLUDED_PREFIXES)


def _provider_for(relative_path: str) -> str:
    if relative_path.startswith((".claude/", ".claude-plugin/")):
        return "claude"
    if relative_path.startswith(".codex/"):
        return "codex"
    if relative_path.startswith(".gemini/") or relative_path == "GEMINI.md":
        return "gemini"
    if relative_path.startswith(".opencode/"):
        return "opencode"
    if relative_path.startswith(".agents/") or relative_path == "AGENTS.md":
        return "agents-generic"
    return "shared"


def _kind_for(relative_path: str) -> str:
    path = PurePosixPath(relative_path)
    parts = set(path.parts)
    name = path.name.lower()
    if name == "skill.md":
        return "skill"
    if "commands" in parts:
        return "command"
    if "prompts" in parts:
        return "prompt"
    if "hooks" in parts or "hook" in name:
        return "hook"
    if name in {"plugin.json", "gemini-extension.json", "verification.yaml"}:
        return "manifest"
    if name in {"agents.md", "claude.md", "gemini.md"}:
        return "instructions"
    if relative_path == "install.sh" or relative_path.startswith("scripts/"):
        return "tooling"
    if name.endswith(("settings.json", "config.toml")):
        return "config"
    return "asset"


def _artifact(root: Path, relative_path: str) -> dict[str, Any]:
    path = root / relative_path
    try:
        stat = path.lstat()
    except FileNotFoundError as exc:
        raise BaselineError(f"tracked path is missing from the checkout: {relative_path}") from exc

    artifact: dict[str, Any] = {
        "path": relative_path,
        "provider": _provider_for(relative_path),
        "kind": _kind_for(relative_path),
        "ownership": "skillz",
        "mode": format(stat.st_mode & 0o777, "04o"),
    }
    if path.is_symlink():
        target = os.readlink(path)
        if Path(target).is_absolute():
            raise BaselineError(f"absolute symlink target is not portable: {relative_path}")
        content = target.encode("utf-8", errors="surrogateescape")
        artifact.update({"type": "symlink", "target": target})
    elif path.is_file():
        content = path.read_bytes()
        artifact["type"] = "file"
    else:
        raise BaselineError(f"unsupported tracked path type: {relative_path}")

    artifact["bytes"] = len(content)
    artifact["sha256"] = hashlib.sha256(content).hexdigest()
    return artifact


def capture_repository(root: Path | str) -> dict[str, Any]:
    """Return a stable, path-relative inventory for a Git checkout."""
    checkout = Path(root).resolve()
    artifacts = [
        _artifact(checkout, relative_path)
        for relative_path in _git_tracked_paths(checkout)
        if _is_distribution_path(relative_path)
    ]
    provider_counts = Counter(item["provider"] for item in artifacts)
    kind_counts = Counter(item["kind"] for item in artifacts)
    return {
        "schema_version": SCHEMA_VERSION,
        "baseline_id": BASELINE_ID,
        "generated_by": GENERATOR,
        "source": {
            "tracked_only": True,
            "included_prefixes": list(INCLUDED_PREFIXES),
            "included_files": sorted(INCLUDED_FILES),
            "excluded_files": sorted(EXCLUDED_FILES),
        },
        "summary": {
            "artifacts": len(artifacts),
            "files": sum(item["type"] == "file" for item in artifacts),
            "symlinks": sum(item["type"] == "symlink" for item in artifacts),
            "by_provider": dict(sorted(provider_counts.items())),
            "by_kind": dict(sorted(kind_counts.items())),
        },
        "artifacts": artifacts,
    }


def render_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _artifact_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["path"]: item for item in payload.get("artifacts", [])}


def check_snapshot(payload: dict[str, Any], snapshot: Path | str) -> list[str]:
    """Describe drift without modifying the expected snapshot."""
    snapshot_path = Path(snapshot)
    if not snapshot_path.is_file():
        return [f"snapshot missing: {snapshot_path.name}"]
    try:
        expected = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"snapshot unreadable: {snapshot_path.name}: {exc}"]

    expected_artifacts = _artifact_map(expected)
    current_artifacts = _artifact_map(payload)
    differences: list[str] = []
    for path in sorted(expected_artifacts.keys() - current_artifacts.keys()):
        differences.append(f"removed: {path}")
    for path in sorted(current_artifacts.keys() - expected_artifacts.keys()):
        differences.append(f"added: {path}")
    for path in sorted(expected_artifacts.keys() & current_artifacts.keys()):
        if expected_artifacts[path] != current_artifacts[path]:
            differences.append(f"modified: {path}")
    if not differences and expected != payload:
        differences.append("snapshot metadata differs")
    return differences


def write_snapshot(payload: dict[str, Any], snapshot: Path | str) -> None:
    """Atomically write a snapshot without exposing a partial file."""
    snapshot_path = Path(snapshot)
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=snapshot_path.parent,
        prefix=f".{snapshot_path.name}.",
        delete=False,
    ) as handle:
        temporary_path = Path(handle.name)
        handle.write(render_json(payload))
    try:
        os.replace(temporary_path, snapshot_path)
    finally:
        temporary_path.unlink(missing_ok=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Git checkout to inventory (defaults to this repository)",
    )
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--write", type=Path, metavar="FILE", help="write the golden snapshot")
    action.add_argument("--check", type=Path, metavar="FILE", help="check an existing snapshot")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        payload = capture_repository(args.root)
        if args.write:
            write_snapshot(payload, args.write)
            print(f"wrote {len(payload['artifacts'])} artifacts to {args.write}")
            return 0
        if args.check:
            differences = check_snapshot(payload, args.check)
            if differences:
                print("distribution baseline drift detected:", file=sys.stderr)
                for difference in differences:
                    print(f"- {difference}", file=sys.stderr)
                return 1
            print(f"distribution baseline matches {args.check}")
            return 0
        sys.stdout.write(render_json(payload))
        return 0
    except BaselineError as exc:
        print(f"baseline capture failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
