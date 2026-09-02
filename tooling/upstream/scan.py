#!/usr/bin/env python3
"""Inventory registered upstream adoption snapshots without network or execution."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
from typing import Any, Iterable


class UpstreamScanError(RuntimeError):
    pass


def _safe_path(root: Path, value: str) -> Path:
    relative = PurePosixPath(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise UpstreamScanError(f"unsafe local snapshot: {value}")
    resolved = (root / relative).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as error:
        raise UpstreamScanError(f"snapshot escapes repository: {value}") from error
    return resolved


def scan_sources(root: Path, registry_path: Path) -> dict[str, Any]:
    root = root.resolve()
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise UpstreamScanError(f"invalid upstream registry: {error}") from error
    if registry.get("schema_version") != 1 or not isinstance(registry.get("sources"), list):
        raise UpstreamScanError("upstream registry must use schema_version 1")
    report_sources: list[dict[str, Any]] = []
    for source in sorted(registry["sources"], key=lambda item: item.get("id", "")):
        if not isinstance(source, dict):
            raise UpstreamScanError("upstream source must be an object")
        if any(key in source for key in ("command", "script", "execute")):
            raise UpstreamScanError(f"executable field forbidden for upstream source: {source.get('id')}")
        if source.get("policy") != "metadata-only-no-network-no-execution":
            raise UpstreamScanError(f"unsafe upstream policy: {source.get('id')}")
        snapshot = _safe_path(root, source["local_snapshot"])
        if not snapshot.is_dir() or snapshot.is_symlink():
            raise UpstreamScanError(f"local snapshot missing: {source['local_snapshot']}")
        files: list[dict[str, Any]] = []
        for path in sorted(candidate for candidate in snapshot.rglob("*") if candidate.is_file()):
            if path.is_symlink():
                raise UpstreamScanError(f"snapshot symlink forbidden: {path}")
            files.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "size": path.stat().st_size,
                }
            )
        report_sources.append(
            {
                "id": source["id"],
                "upstream_url": source["upstream_url"],
                "ref": source["ref"],
                "policy": source["policy"],
                "files": files,
            }
        )
    return {"schema_version": 1, "mode": "read-only", "sources": report_sources}


def render_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--registry", type=Path, default=Path("tooling/upstream/sources.yaml"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    registry = args.registry if args.registry.is_absolute() else args.root / args.registry
    try:
        rendered = render_report(scan_sources(args.root.resolve(), registry))
        if args.output is None:
            print(rendered, end="")
            return 0
        output = args.output if args.output.is_absolute() else args.root / args.output
        if args.check:
            if not output.is_file() or output.read_text(encoding="utf-8") != rendered:
                print("upstream inventory is stale", file=sys.stderr)
                return 1
            print("upstream inventory is fresh")
            return 0
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        print(f"wrote {output}")
        return 0
    except (UpstreamScanError, OSError, KeyError) as error:
        print(f"upstream scan failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
