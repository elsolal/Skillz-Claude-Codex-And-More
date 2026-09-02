#!/usr/bin/env python3
"""Create and verify deterministic provider distribution goldens."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


class GoldenError(RuntimeError):
    pass


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GoldenError(f"invalid {label}: {path}: {error}") from error
    if not isinstance(payload, dict):
        raise GoldenError(f"{label} must be an object: {path}")
    return payload


def _frontmatter(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return {}
    if not lines or lines[0].strip() != "---":
        return {}
    result: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line or line.startswith((" ", "\t")):
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip('"\'')
    return dict(sorted(result.items()))


def snapshot_distribution(dist_root: Path) -> dict[str, Any]:
    dist_root = Path(dist_root).resolve()
    report = _load_json(dist_root / "build-report.json", "build report")
    provider_names = report.get("providers")
    if not isinstance(provider_names, list) or not all(isinstance(item, str) for item in provider_names):
        raise GoldenError("build report providers are invalid")
    providers: dict[str, Any] = {}
    for provider in sorted(provider_names):
        root = dist_root / provider
        if root.is_symlink() or not root.is_dir():
            raise GoldenError(f"provider output is missing: {provider}")
        files: list[dict[str, Any]] = []
        skills: list[dict[str, Any]] = []
        manifests: list[dict[str, Any]] = []
        for path in sorted(root.rglob("*")):
            if path.is_symlink():
                raise GoldenError(f"provider output contains a symlink: {path}")
            if path.is_dir():
                continue
            if not path.is_file():
                raise GoldenError(f"provider output contains a special file: {path}")
            relative = path.relative_to(root).as_posix()
            files.append(
                {
                    "path": relative,
                    "mode": f"{path.stat().st_mode & 0o777:04o}",
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
            if path.name == "SKILL.md":
                skills.append({"path": relative, "frontmatter": _frontmatter(path)})
            if path.name in {"plugin.json", "marketplace.json"}:
                manifests.append({"path": relative, "payload": _load_json(path, "provider manifest")})
        aliases = [
            {
                "artifact_id": item.get("artifact_id"),
                "type": item.get("type"),
                "alias": item.get("alias"),
                "output": str(item.get("output", ""))[len(provider) + 1 :],
            }
            for item in report.get("artifacts", [])
            if isinstance(item, dict)
            and item.get("provider") == provider
            and item.get("status") == "supported"
        ]
        providers[provider] = {
            "files": files,
            "skills": skills,
            "manifests": manifests,
            "aliases": sorted(aliases, key=lambda item: (str(item["type"]), str(item["alias"]))),
        }
    return {
        "schema_version": 1,
        "distribution": report.get("distribution"),
        "tree_hash": report.get("tree_hash"),
        "providers": providers,
    }


def _file_index(snapshot: dict[str, Any]) -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    providers = snapshot.get("providers", {})
    if not isinstance(providers, dict):
        return result
    for provider, payload in providers.items():
        if not isinstance(payload, dict):
            continue
        for item in payload.get("files", []):
            if isinstance(item, dict) and isinstance(item.get("path"), str):
                result[f"{provider}/{item['path']}"] = (
                    str(item.get("mode")),
                    str(item.get("sha256")),
                )
    return result


def compare_snapshots(expected: dict[str, Any], actual: dict[str, Any]) -> list[str]:
    expected_files = _file_index(expected)
    actual_files = _file_index(actual)
    differences: list[str] = []
    for path in sorted(set(expected_files) | set(actual_files)):
        if path not in actual_files:
            differences.append(f"removed: {path}")
        elif path not in expected_files:
            differences.append(f"added: {path}")
        elif expected_files[path] != actual_files[path]:
            differences.append(f"modified: {path}")
    for key in ("distribution", "tree_hash"):
        if expected.get(key) != actual.get(key):
            differences.append(f"metadata: {key}")
    for provider in sorted(set(expected.get("providers", {})) | set(actual.get("providers", {}))):
        for key in ("skills", "manifests", "aliases"):
            expected_value = expected.get("providers", {}).get(provider, {}).get(key)
            actual_value = actual.get("providers", {}).get(provider, {}).get(key)
            if expected_value != actual_value:
                differences.append(f"metadata: {provider}/{key}")
    return differences


def write_golden(path: Path, snapshot: dict[str, Any], *, approved: bool) -> None:
    if not approved:
        raise GoldenError("golden update requires explicit review approval")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def scan_neutral_contracts(root: Path) -> list[str]:
    forbidden = (".claude/", "claude code", '"provider": "claude"')
    findings: list[str] = []
    for path in sorted(Path(root).rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        content = path.read_text(encoding="utf-8").lower()
        for token in forbidden:
            if token in content:
                findings.append(f"{path.name}: {token}")
    return findings


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist-root", type=Path, default=Path("dist"))
    parser.add_argument("--output", type=Path, required=True)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true")
    action.add_argument("--update", action="store_true")
    parser.add_argument("--approve-review", action="store_true")
    args = parser.parse_args(argv)
    try:
        snapshot = snapshot_distribution(args.dist_root)
        if args.update:
            write_golden(args.output, snapshot, approved=args.approve_review)
            print(f"wrote reviewed golden: {args.output}")
            return 0
        expected = _load_json(args.output, "distribution golden")
        differences = compare_snapshots(expected, snapshot)
        if differences:
            raise GoldenError("distribution golden drift: " + "; ".join(differences))
        print(f"distribution golden is fresh: {args.output}")
        return 0
    except (GoldenError, OSError) as error:
        print(f"golden verification failed: {error}", file=__import__("sys").stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
