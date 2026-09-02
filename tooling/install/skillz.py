#!/usr/bin/env python3
"""CLI for manifest-owned Skillz bundle installation and diagnostics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Iterable

from manager import (
    DEFAULT_BACKUP_LIMIT,
    InstallConflict,
    InstallError,
    doctor_target,
    install_bundle,
    restore_target,
    uninstall_target,
)


def _render_human(payload: dict[str, Any]) -> str:
    lines = [f"status: {payload.get('status', 'unknown')}"]
    if "runtime" in payload and isinstance(payload["runtime"], str):
        lines.append(f"runtime: {payload['runtime']}")
    if "release" in payload:
        lines.append(f"release: {payload['release']}")
    runtime = payload.get("runtime")
    if isinstance(runtime, dict):
        lines.append(
            f"runtime: {runtime.get('binary')} "
            f"({'detected' if runtime.get('detected') else 'missing'})"
        )
        if runtime.get("version"):
            lines.append(f"version: {runtime['version']}")
    certification = payload.get("certification")
    if isinstance(certification, dict):
        lines.append(
            f"certification: {certification.get('level')} "
            f"(package={certification.get('package')}, drift={certification.get('version_drift')})"
        )
    for action in payload.get("actions", []):
        if isinstance(action, dict):
            lines.append(f"{action.get('action')}: {action.get('path')}")
    for item in payload.get("files", []):
        if isinstance(item, dict) and item.get("state") != "ok":
            lines.append(f"{item.get('state')}: {item.get('path')}")
    for repair in payload.get("repairs", []):
        lines.append(f"repair: {repair}")
    return "\n".join(lines)


def _common_install(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--dist-root", type=Path, default=Path("dist"))
    parser.add_argument("--runtime", required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--backup-limit", type=int, default=DEFAULT_BACKUP_LIMIT)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", dest="json_output")
    subparsers = parser.add_subparsers(dest="command", required=True)
    _common_install(subparsers.add_parser("install"))
    _common_install(subparsers.add_parser("update"))
    for name in ("uninstall", "restore"):
        operation = subparsers.add_parser(name)
        operation.add_argument("--target", type=Path, required=True)
        operation.add_argument("--dry-run", action="store_true")
    doctor = subparsers.add_parser("doctor")
    doctor.add_argument("--dist-root", type=Path, default=Path("dist"))
    doctor.add_argument("--runtime", required=True)
    doctor.add_argument("--target", type=Path, required=True)
    doctor.add_argument("--runtime-binary")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command in {"install", "update"}:
            payload = install_bundle(
                args.dist_root,
                args.target,
                args.runtime,
                mode=args.command,
                dry_run=args.dry_run,
                backup_limit=args.backup_limit,
            )
        elif args.command == "uninstall":
            payload = uninstall_target(args.target, dry_run=args.dry_run)
        elif args.command == "restore":
            payload = restore_target(args.target, dry_run=args.dry_run)
        else:
            payload = doctor_target(
                args.dist_root,
                args.target,
                args.runtime,
                runtime_binary=args.runtime_binary,
            )
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json_output else _render_human(payload))
        return 0 if payload.get("status") not in {"broken"} else 2
    except (InstallConflict, InstallError, OSError) as error:
        payload = {
            "status": "conflict" if isinstance(error, InstallConflict) else "error",
            "error": str(error),
        }
        print(
            json.dumps(payload, indent=2, sort_keys=True) if args.json_output else _render_human(payload) + f"\nerror: {error}",
            file=sys.stderr,
        )
        return 2 if isinstance(error, InstallConflict) else 1


if __name__ == "__main__":
    raise SystemExit(main())
