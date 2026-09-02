#!/usr/bin/env python3
"""Certify the manifest installer lifecycle against complete P0 bundles."""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


P0_RUNTIMES = ("claude", "codex", "opencode", "agents-generic")


class CertificationError(RuntimeError):
    pass


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        metadata = path.lstat()
        if path.is_symlink():
            entry_type = b"symlink"
        elif path.is_file():
            entry_type = b"file"
        elif path.is_dir():
            entry_type = b"directory"
        else:
            entry_type = b"other"
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(entry_type)
        digest.update(b"\0")
        digest.update(str(stat.S_IMODE(metadata.st_mode)).encode("ascii"))
        digest.update(b"\0")
        if entry_type == b"symlink":
            digest.update(path.readlink().as_posix().encode("utf-8"))
        elif entry_type == b"file":
            digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _run(root: Path, arguments: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        [str(root / "bin" / "skillz"), "--json", *arguments],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise CertificationError(
            f"skillz {' '.join(arguments[:1])} failed with {completed.returncode}: "
            f"{completed.stderr.strip()}"
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise CertificationError(f"skillz output is not JSON: {error}") from error
    if not isinstance(payload, dict):
        raise CertificationError("skillz output is not an object")
    return payload


def _certify_runtime(root: Path, temporary: Path, runtime: str) -> dict[str, Any]:
    target = temporary / f"{runtime} target with spaces"
    common = ["--dist-root", str(root / "dist"), "--runtime", runtime, "--target", str(target)]
    dry_install = _run(root, ["install", *common, "--dry-run"])
    if target.exists():
        raise CertificationError(f"dry-run created target for {runtime}")
    installed = _run(root, ["install", *common])
    manifest_path = target / ".skillz" / "install-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    user_file = target / "user-owned.txt"
    user_file.write_text("preserve me\n", encoding="utf-8")

    dry_update = _run(root, ["update", *common, "--dry-run"])
    updated = _run(root, ["update", *common])
    before_doctor = _tree_digest(target)
    doctor = _run(root, ["doctor", *common, "--runtime-binary", "true"])
    if _tree_digest(target) != before_doctor:
        raise CertificationError(f"doctor mutated target for {runtime}")
    file_states = {item["state"] for item in doctor.get("files", [])}
    if file_states != {"ok"}:
        raise CertificationError(f"doctor found non-ok files for {runtime}: {sorted(file_states)}")

    dry_uninstall = _run(root, ["uninstall", "--target", str(target), "--dry-run"])
    uninstalled = _run(root, ["uninstall", "--target", str(target)])
    if not user_file.is_file() or user_file.read_text(encoding="utf-8") != "preserve me\n":
        raise CertificationError(f"uninstall removed user file for {runtime}")
    if manifest_path.exists():
        raise CertificationError(f"uninstall retained active manifest for {runtime}")

    serialized_evidence = json.dumps(
        [
            manifest,
            dry_install,
            installed,
            dry_update,
            updated,
            doctor,
            dry_uninstall,
            uninstalled,
        ],
        sort_keys=True,
    )
    if str(target) in serialized_evidence:
        raise CertificationError(f"installer recorded absolute target for {runtime}")

    return {
        "runtime": runtime,
        "bundle_release": manifest["release"],
        "managed_files": len(manifest["files"]),
        "install_dry_run": dry_install["status"],
        "install": installed["status"],
        "update_dry_run": dry_update["status"],
        "update": updated["status"],
        "doctor": {
            "status": doctor["status"],
            "all_files_ok": True,
            "mutation_free": True,
            "runtime_probe": "true --version (synthetic installer-only probe)",
        },
        "uninstall_dry_run": dry_uninstall["status"],
        "uninstall": uninstalled["status"],
        "user_file_preserved": True,
        "absolute_target_recorded": False,
    }


def certify(root: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="skillz-install-cert-") as temporary_name:
        temporary = Path(temporary_name)
        results = [_certify_runtime(root, temporary, runtime) for runtime in P0_RUNTIMES]
    return {
        "schema_version": 1,
        "status": "PASS",
        "scope": "installer-lifecycle-only",
        "runtime_certification_claim": "none",
        "network_used": False,
        "p0_runtimes": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output if args.output.is_absolute() else root / args.output
    try:
        report = certify(root)
    except CertificationError as error:
        print(f"installer lifecycle certification failed: {error}", file=sys.stderr)
        return 1
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not output.is_file() or output.read_text(encoding="utf-8") != rendered:
            print(f"installer lifecycle report is stale: {output}", file=sys.stderr)
            return 1
        print(f"installer lifecycle certification is fresh: {output}")
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    print(f"wrote installer lifecycle certification: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
