#!/usr/bin/env python3
"""Manifest-owned, transactional installer for compiled Skillz provider bundles."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tempfile
from typing import Any
import uuid


MANIFEST_RELATIVE = PurePosixPath(".skillz/install-manifest.json")
BACKUPS_RELATIVE = PurePosixPath(".skillz/backups")
MANIFEST_SCHEMA_VERSION = 1
DEFAULT_BACKUP_LIMIT = 3
RUNTIME_BINARIES = {
    "claude": "claude",
    "codex": "codex",
    "opencode": "opencode",
}


class InstallError(RuntimeError):
    pass


class InstallConflict(InstallError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _hash_bytes(content: bytes) -> str:
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def _hash_file(path: Path) -> str:
    return _hash_bytes(path.read_bytes())


def _safe_relative(value: str) -> PurePosixPath:
    relative = PurePosixPath(value)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise InstallError(f"unsafe relative path: {value}")
    return relative


def _target_path(target: Path, relative: str) -> Path:
    pure = _safe_relative(relative)
    path = target.joinpath(*pure.parts)
    current = target
    for part in pure.parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise InstallConflict(f"unverifiable symlink parent: {relative}")
    return path


def _normalize_target(target: Path) -> Path:
    raw = Path(target).absolute()
    if raw.is_symlink():
        raise InstallConflict(f"unverifiable target symlink: {raw}")
    resolved = raw.resolve()
    state_root = resolved / ".skillz"
    if state_root.is_symlink():
        raise InstallConflict("unverifiable .skillz state symlink")
    return resolved


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise InstallError(f"invalid {label}: {path}: {error}") from error
    if not isinstance(payload, dict):
        raise InstallError(f"{label} must be a JSON object: {path}")
    return payload


def _read_manifest(target: Path, *, required: bool) -> dict[str, Any] | None:
    path = target / Path(MANIFEST_RELATIVE)
    if path.is_symlink():
        raise InstallConflict("unverifiable installation manifest symlink")
    if not path.exists():
        if required:
            raise InstallError(f"installation manifest is missing: {path}")
        return None
    manifest = _load_json(path, "installation manifest")
    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise InstallError("unsupported installation manifest schema")
    files = manifest.get("files")
    if not isinstance(files, list):
        raise InstallError("installation manifest files must be a list")
    seen: set[str] = set()
    for item in files:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise InstallError("invalid installation manifest file entry")
        relative = item["path"]
        _safe_relative(relative)
        if relative in seen:
            raise InstallError(f"duplicate installation manifest path: {relative}")
        seen.add(relative)
        if item.get("ownership") != "skillz" or item.get("merge_strategy") != "replace_owned":
            raise InstallError(f"unsupported ownership contract: {relative}")
        installed_hash = item.get("installed_hash")
        if not isinstance(installed_hash, str) or not installed_hash.startswith("sha256:"):
            raise InstallError(f"invalid installed hash: {relative}")
    return manifest


def _bundle_inventory(dist_root: Path, runtime: str) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    dist_root = dist_root.resolve()
    report = _load_json(dist_root / "build-report.json", "build report")
    distribution = report.get("distribution")
    if not isinstance(distribution, dict) or not isinstance(distribution.get("version"), str):
        raise InstallError("build report has no distribution identity")
    runtime_root = dist_root / runtime
    if runtime_root.is_symlink() or not runtime_root.is_dir():
        raise InstallError(f"compiled runtime bundle is missing: {runtime}")
    source_ids: dict[str, tuple[str, str]] = {}
    for artifact in report.get("artifacts", []):
        if not isinstance(artifact, dict) or artifact.get("provider") != runtime:
            continue
        output = artifact.get("output")
        if not isinstance(output, str) or not output.startswith(f"{runtime}/"):
            continue
        source_ids[output[len(runtime) + 1 :]] = (
            str(artifact.get("type", "artifact")),
            str(artifact.get("artifact_id", "unknown")),
        )
    for package in report.get("packages", []):
        if not isinstance(package, dict) or package.get("provider") != runtime:
            continue
        for key in ("manifest", "marketplace"):
            output = package.get(key)
            if isinstance(output, str) and output.startswith(f"{runtime}/"):
                source_ids[output[len(runtime) + 1 :]] = ("package", runtime)

    inventory: dict[str, dict[str, Any]] = {}
    for path in sorted(runtime_root.rglob("*")):
        if path.is_symlink():
            raise InstallError(f"compiled bundle contains a symlink: {path}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise InstallError(f"compiled bundle contains a special file: {path}")
        relative = path.relative_to(runtime_root).as_posix()
        _safe_relative(relative)
        if PurePosixPath(relative).parts[0] == ".skillz":
            raise InstallError(f"compiled bundle uses reserved installer state: {relative}")
        artifact_type, source_name = source_ids.get(relative, ("generated", relative))
        inventory[relative] = {
            "source": path,
            "source_id": f"{artifact_type}.{source_name}",
            "artifact": artifact_type,
            "source_hash": _hash_file(path),
            "mode": path.stat().st_mode & 0o777,
        }
    if not inventory:
        raise InstallError(f"compiled runtime bundle is empty: {runtime}")
    return distribution, inventory


def _file_state(path: Path, expected_hash: str) -> str:
    if path.is_symlink():
        return "unverifiable"
    if not path.exists():
        return "missing"
    if not path.is_file():
        return "unverifiable"
    return "current" if _hash_file(path) == expected_hash else "modified"


def _atomic_write(path: Path, content: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_name, mode)
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def _remove_file_and_empty_parents(path: Path, target: Path) -> None:
    if path.is_symlink() or path.exists():
        path.unlink()
    parent = path.parent
    state_root = target / ".skillz"
    while parent != target and parent != state_root:
        try:
            parent.rmdir()
        except OSError:
            break
        parent = parent.parent


def _snapshot(
    target: Path,
    install_id: str,
    relative_paths: list[str],
    previous_manifest: dict[str, Any] | None,
) -> Path:
    backup_root = target / Path(BACKUPS_RELATIVE) / install_id
    if backup_root.exists() or backup_root.is_symlink():
        raise InstallError(f"backup already exists: {install_id}")
    backup_root.mkdir(parents=True)
    entries: list[dict[str, Any]] = []
    for relative in sorted(set(relative_paths)):
        path = _target_path(target, relative)
        state = {
            "path": relative,
            "existed": path.exists(),
        }
        if path.exists():
            backup = backup_root / "files" / Path(relative)
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup)
            state.update({"mode": path.stat().st_mode & 0o777, "hash": _hash_file(path)})
        entries.append(state)
    if previous_manifest is not None:
        (backup_root / "previous-manifest.json").write_text(
            json.dumps(previous_manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    state_payload = {
        "schema_version": 1,
        "created_at": _now(),
        "previous_manifest": previous_manifest is not None,
        "files": entries,
    }
    (backup_root / "state.json").write_text(
        json.dumps(state_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return backup_root


def _apply_snapshot(target: Path, backup_root: Path) -> None:
    state = _load_json(backup_root / "state.json", "backup state")
    entries = state.get("files")
    if not isinstance(entries, list):
        raise InstallError("backup state files must be a list")
    for item in entries:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise InstallError("invalid backup state entry")
        relative = item["path"]
        path = _target_path(target, relative)
        if item.get("existed") is True:
            backup = backup_root / "files" / Path(relative)
            if not backup.is_file() or backup.is_symlink():
                raise InstallError(f"backup payload missing: {relative}")
            _atomic_write(path, backup.read_bytes(), int(item.get("mode", 0o644)))
        else:
            _remove_file_and_empty_parents(path, target)
    manifest_path = target / Path(MANIFEST_RELATIVE)
    previous_manifest_path = backup_root / "previous-manifest.json"
    if state.get("previous_manifest") is True:
        previous_content = previous_manifest_path.read_bytes()
        _atomic_write(manifest_path, previous_content, 0o600)
    else:
        _remove_file_and_empty_parents(manifest_path, target)


def _prune_backups(target: Path, limit: int) -> None:
    backups = target / Path(BACKUPS_RELATIVE)
    if not backups.is_dir() or backups.is_symlink():
        return
    candidates: list[tuple[str, Path]] = []
    for directory in backups.iterdir():
        if not directory.is_dir() or directory.is_symlink():
            continue
        try:
            state = _load_json(directory / "state.json", "backup state")
            candidates.append((str(state.get("created_at", "")), directory))
        except InstallError:
            continue
    for _, directory in sorted(candidates)[:-max(limit, 1)]:
        shutil.rmtree(directory)


def _plan_install_actions(
    target: Path,
    inventory: dict[str, dict[str, Any]],
    previous_files: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    conflicts: list[str] = []
    actions: list[dict[str, str]] = []
    for relative in sorted(inventory):
        path = _target_path(target, relative)
        owned = previous_files.get(relative)
        if owned is not None:
            state = _file_state(path, owned["installed_hash"])
            if state in {"modified", "unverifiable"}:
                conflicts.append(f"{state}: {relative}")
            else:
                action = "replace" if state == "current" else "repair"
                actions.append({"action": action, "path": relative})
        elif path.is_symlink() or path.exists():
            state = "unverifiable" if path.is_symlink() or not path.is_file() else "unexpected"
            conflicts.append(f"{state}: {relative}")
        else:
            actions.append({"action": "add", "path": relative})
    for relative, owned in sorted(previous_files.items()):
        if relative in inventory:
            continue
        state = _file_state(_target_path(target, relative), owned["installed_hash"])
        if state in {"modified", "unverifiable"}:
            conflicts.append(f"{state}: {relative}")
        else:
            action = "remove" if state == "current" else "forget"
            actions.append({"action": action, "path": relative})
    if conflicts:
        raise InstallConflict("installation conflicts: " + "; ".join(conflicts))
    return actions


def _install_manifest_entry(
    target: Path,
    relative: str,
    source: dict[str, Any],
) -> dict[str, Any]:
    destination = _target_path(target, relative)
    _atomic_write(destination, source["source"].read_bytes(), source["mode"])
    return {
        "path": relative,
        "artifact": source["artifact"],
        "source_id": source["source_id"],
        "source_hash": source["source_hash"],
        "installed_hash": _hash_file(destination),
        "mode": f"{source['mode']:04o}",
        "ownership": "skillz",
        "merge_strategy": "replace_owned",
    }


def _apply_installation(
    target: Path,
    runtime: str,
    release: str,
    inventory: dict[str, dict[str, Any]],
    actions: list[dict[str, str]],
    previous: dict[str, Any] | None,
    backup_limit: int,
) -> str:
    install_id = str(uuid.uuid4())
    target.mkdir(parents=True, exist_ok=True)
    backup_root = _snapshot(target, install_id, [item["path"] for item in actions], previous)
    try:
        for action in actions:
            if action["action"] in {"remove", "forget"}:
                _remove_file_and_empty_parents(_target_path(target, action["path"]), target)
        manifest = {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "install_id": install_id,
            "previous_install_id": (previous or {}).get("install_id"),
            "release": release,
            "runtime": runtime,
            "installed_at": _now(),
            "files": [
                _install_manifest_entry(target, relative, source)
                for relative, source in sorted(inventory.items())
            ],
        }
        _atomic_write(
            target / Path(MANIFEST_RELATIVE),
            (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"),
            0o600,
        )
    except Exception:
        _apply_snapshot(target, backup_root)
        raise
    _prune_backups(target, backup_limit)
    return install_id


def install_bundle(
    dist_root: Path,
    target: Path,
    runtime: str,
    *,
    mode: str,
    dry_run: bool = False,
    backup_limit: int = DEFAULT_BACKUP_LIMIT,
) -> dict[str, Any]:
    if mode not in {"install", "update"}:
        raise InstallError(f"invalid install mode: {mode}")
    dist_root = Path(dist_root)
    target = _normalize_target(Path(target))
    distribution, inventory = _bundle_inventory(dist_root, runtime)
    previous = _read_manifest(target, required=mode == "update")
    if mode == "install" and previous is not None:
        raise InstallError("installation already exists; use update")
    if previous is not None and previous.get("runtime") != runtime:
        raise InstallConflict(
            f"runtime mismatch: installed={previous.get('runtime')} requested={runtime}"
        )
    previous_files = {
        item["path"]: item for item in (previous or {}).get("files", []) if isinstance(item, dict)
    }
    actions = _plan_install_actions(target, inventory, previous_files)
    result = {
        "status": "dry-run" if dry_run else "installed" if mode == "install" else "updated",
        "operation": mode,
        "runtime": runtime,
        "release": distribution["version"],
        "actions": actions,
    }
    if dry_run:
        return result

    install_id = _apply_installation(
        target,
        runtime,
        distribution["version"],
        inventory,
        actions,
        previous,
        backup_limit,
    )
    result["install_id"] = install_id
    return result


def _assert_manifest_files_unmodified(target: Path, manifest: dict[str, Any]) -> None:
    conflicts: list[str] = []
    for item in manifest["files"]:
        state = _file_state(_target_path(target, item["path"]), item["installed_hash"])
        if state in {"modified", "unverifiable"}:
            conflicts.append(f"{state}: {item['path']}")
    if conflicts:
        raise InstallConflict("managed files changed: " + "; ".join(conflicts))


def uninstall_target(target: Path, *, dry_run: bool = False) -> dict[str, Any]:
    target = _normalize_target(Path(target))
    manifest = _read_manifest(target, required=True)
    assert manifest is not None
    _assert_manifest_files_unmodified(target, manifest)
    actions = [
        {"action": "remove", "path": item["path"]}
        for item in sorted(manifest["files"], key=lambda entry: entry["path"])
    ]
    if dry_run:
        return {"status": "dry-run", "operation": "uninstall", "actions": actions}
    for action in actions:
        _remove_file_and_empty_parents(_target_path(target, action["path"]), target)
    _remove_file_and_empty_parents(target / Path(MANIFEST_RELATIVE), target)
    return {"status": "uninstalled", "operation": "uninstall", "actions": actions}


def restore_target(target: Path, *, dry_run: bool = False) -> dict[str, Any]:
    target = _normalize_target(Path(target))
    manifest = _read_manifest(target, required=True)
    assert manifest is not None
    _assert_manifest_files_unmodified(target, manifest)
    install_id = manifest.get("install_id")
    if not isinstance(install_id, str):
        raise InstallError("installation manifest has no install_id")
    backup_root = target / Path(BACKUPS_RELATIVE) / install_id
    if not backup_root.is_dir() or backup_root.is_symlink():
        raise InstallError(f"restore backup is missing: {install_id}")
    state = _load_json(backup_root / "state.json", "backup state")
    actions = [
        {"action": "restore" if item.get("existed") else "remove", "path": item["path"]}
        for item in state.get("files", [])
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    ]
    if dry_run:
        return {"status": "dry-run", "operation": "restore", "actions": actions}
    _apply_snapshot(target, backup_root)
    return {"status": "restored", "operation": "restore", "actions": actions}


def _runtime_status(runtime: str, runtime_binary: str | None) -> dict[str, Any]:
    binary = runtime_binary or RUNTIME_BINARIES.get(runtime, runtime)
    resolved = shutil.which(binary)
    if resolved is None:
        return {"binary": binary, "detected": False, "version": None}
    completed = subprocess.run(
        [resolved, "--version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    output = completed.stdout.strip() or completed.stderr.strip()
    return {
        "binary": binary,
        "detected": completed.returncode == 0,
        "version": output if completed.returncode == 0 else None,
    }


def _certification_status(dist_root: Path, runtime: str, runtime_version: str | None) -> dict[str, Any]:
    capabilities_path = dist_root.resolve().parent / "providers" / runtime / "capabilities.yaml"
    if not capabilities_path.is_file():
        return {
            "level": "unknown",
            "package": "unknown",
            "version_observed": None,
            "version_drift": None,
        }
    capabilities = _load_json(capabilities_path, "provider capabilities")
    runtime_contract = capabilities.get("runtime")
    observed = runtime_contract.get("version_observed") if isinstance(runtime_contract, dict) else None
    version_drift = None
    if isinstance(observed, str) and runtime_version is not None:
        version_drift = observed not in runtime_version
    return {
        "level": capabilities.get("certification", "unknown"),
        "package": capabilities.get("package", "unknown"),
        "version_observed": observed,
        "version_drift": version_drift,
    }


def doctor_target(
    dist_root: Path,
    target: Path,
    runtime: str,
    *,
    runtime_binary: str | None = None,
) -> dict[str, Any]:
    target = _normalize_target(Path(target))
    distribution, inventory = _bundle_inventory(Path(dist_root), runtime)
    manifest = _read_manifest(target, required=False)
    manifest_files = {
        item["path"]: item for item in (manifest or {}).get("files", []) if isinstance(item, dict)
    }
    files: list[dict[str, str]] = []
    for relative in sorted(set(manifest_files) | set(inventory)):
        owned = manifest_files.get(relative)
        expected = inventory.get(relative)
        path = _target_path(target, relative)
        if owned is not None and expected is None:
            state = "orphaned"
        elif owned is None:
            if path.is_symlink() or (path.exists() and not path.is_file()):
                state = "unverifiable"
            elif path.exists():
                state = "unexpected"
            else:
                state = "missing"
        else:
            state = _file_state(path, owned["installed_hash"])
            if state == "current":
                state = "ok"
        files.append({"path": relative, "state": state})
    runtime_status = _runtime_status(runtime, runtime_binary)
    certification = _certification_status(Path(dist_root), runtime, runtime_status["version"])
    broken_states = {"missing", "modified", "unexpected", "orphaned", "unverifiable"}
    broken = not runtime_status["detected"] or any(item["state"] in broken_states for item in files)
    summary = {
        state: sum(1 for item in files if item["state"] == state)
        for state in ("ok", "missing", "modified", "unexpected", "orphaned", "unverifiable")
    }
    repairs: list[str] = []
    if not runtime_status["detected"]:
        repairs.append(f"install or expose the {runtime_status['binary']} runtime on PATH")
    if manifest is None:
        repairs.append(f"run skillz install --runtime {runtime} with an explicit --target")
    if any(summary[state] for state in ("modified", "unexpected", "unverifiable")):
        repairs.append("resolve file conflicts explicitly before update, uninstall or restore")
    if summary["missing"] or summary["orphaned"]:
        repairs.append(f"run skillz update --runtime {runtime} after reviewing the dry-run")
    runtime_mismatch = manifest is not None and manifest.get("runtime") != runtime
    release_drift = manifest is not None and manifest.get("release") != distribution["version"]
    partial = bool(certification.get("version_drift") or runtime_mismatch or release_drift)
    if runtime_mismatch:
        repairs.append("select the runtime recorded by the manifest or use a separate target")
    if release_drift:
        repairs.append(f"review and run skillz update for release {distribution['version']}")
    status = "broken" if broken or runtime_mismatch else "partial" if partial else "healthy"
    return {
        "schema_version": 1,
        "status": status,
        "runtime": runtime_status,
        "certification": certification,
        "release_expected": distribution["version"],
        "release_installed": (manifest or {}).get("release"),
        "release_drift": release_drift,
        "runtime_mismatch": runtime_mismatch,
        "manifest_present": manifest is not None,
        "summary": summary,
        "files": files,
        "repairs": repairs,
    }
