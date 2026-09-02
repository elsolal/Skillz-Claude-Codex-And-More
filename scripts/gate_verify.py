#!/usr/bin/env python3
"""Seal and mechanically verify D-EPCT quality gate v2 envelopes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
from typing import Any, Iterable


SCHEMA_VERSION = 2
PROOF_SCHEMA_VERSION = 1
ZERO_HASH = "0" * 64
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
INTEGRITY_RE = re.compile(
    rb'(?m)^integrity_sha256:[ \t]*"([0-9a-f]{64})"[ \t]*$'
)
ALLOWED_CODE_EXCLUSIONS = {"CHANGELOG.md"}
GATE_FIELDS = {
    "schema_version",
    "verdict",
    "level",
    "base_sha",
    "head_sha",
    "code_diff_hash",
    "code_diff_exclusions",
    "proof_payload",
    "proof_payload_hash",
    "integrity_sha256",
}


class GateVerificationError(RuntimeError):
    pass


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _scalar(content: str, key: str) -> Any:
    match = re.search(rf"^{re.escape(key)}:\s*(.+?)\s*$", content, re.MULTILINE)
    if not match:
        raise GateVerificationError(f"missing required field: {key}")
    raw = match.group(1)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def _verify_closed_gate_shape(content: str) -> None:
    fields = re.findall(r"^([A-Za-z][A-Za-z0-9_]*):", content, re.MULTILINE)
    duplicates = sorted({field for field in fields if fields.count(field) > 1})
    if duplicates:
        raise GateVerificationError(f"duplicate gate fields: {duplicates}")
    unknown = sorted(set(fields) - GATE_FIELDS)
    missing = sorted(GATE_FIELDS - set(fields))
    if unknown:
        raise GateVerificationError(f"unknown gate fields: {unknown}")
    if missing:
        raise GateVerificationError(f"missing required gate fields: {missing}")


def _safe_relative(root: Path, value: str, prefix: str) -> Path:
    pure = PurePosixPath(value)
    if pure.is_absolute() or ".." in pure.parts or not value.startswith(prefix):
        raise GateVerificationError(f"unsafe evidence path: {value}")
    resolved = (root / pure).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as error:
        raise GateVerificationError(f"evidence path escapes repository: {value}") from error
    return resolved


def _normalized_gate_bytes(content: bytes) -> bytes:
    matches = list(INTEGRITY_RE.finditer(content))
    if len(matches) != 1:
        raise GateVerificationError("gate must contain exactly one integrity_sha256 field")
    return INTEGRITY_RE.sub(
        f'integrity_sha256: "{ZERO_HASH}"'.encode("ascii"),
        content,
        count=1,
    )


def seal_gate(gate_path: Path) -> str:
    content = gate_path.read_bytes()
    normalized = _normalized_gate_bytes(content)
    integrity = hashlib.sha256(normalized).hexdigest()
    sealed = INTEGRITY_RE.sub(
        f'integrity_sha256: "{integrity}"'.encode("ascii"),
        content,
        count=1,
    )
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{gate_path.name}.", dir=gate_path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(sealed)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, gate_path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)
    return integrity


def compute_code_diff_hash(
    root: Path,
    base_sha: str,
    head_sha: str,
    exclusions: list[str],
) -> str:
    unknown = set(exclusions) - ALLOWED_CODE_EXCLUSIONS
    if unknown:
        raise GateVerificationError(f"unsupported code diff exclusions: {sorted(unknown)}")
    command = ["diff", f"{base_sha}...{head_sha}", "--", "."]
    command.extend(f":(exclude){path}" for path in sorted(exclusions))
    completed = _git(root, *command)
    return hashlib.sha256(completed.stdout).hexdigest()


def _manifest_commands(manifest_path: Path) -> tuple[str, dict[str, str]]:
    content = manifest_path.read_text(encoding="utf-8")
    fingerprint = re.search(
        r'^config_fingerprint:\s*["\']?([^"\'\n]+)',
        content,
        re.MULTILINE,
    )
    if not fingerprint:
        raise GateVerificationError("verification manifest has no config_fingerprint")
    commands: dict[str, str] = {}
    in_commands = False
    for line in content.splitlines():
        if line == "commands:":
            in_commands = True
            continue
        if not in_commands:
            continue
        if line and not line.startswith("  "):
            break
        match = re.match(r"^  ([A-Za-z0-9_-]+):\s*(.+)$", line)
        if not match:
            continue
        try:
            value = json.loads(match.group(2))
        except json.JSONDecodeError as error:
            raise GateVerificationError(f"manifest command is not a quoted scalar: {match.group(1)}") from error
        if not isinstance(value, str):
            raise GateVerificationError(f"manifest command is not a string: {match.group(1)}")
        commands[match.group(1)] = value
    return fingerprint.group(1), commands


def _load_unique_json(path: Path) -> dict[str, Any]:
    def unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise GateVerificationError(f"duplicate JSON key in proof payload: {key}")
            result[key] = value
        return result

    try:
        payload = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_pairs)
    except json.JSONDecodeError as error:
        raise GateVerificationError(f"invalid proof payload JSON: {error.msg}") from error
    if not isinstance(payload, dict):
        raise GateVerificationError("proof payload must be a JSON object")
    return payload


def _verify_executions(payload: dict[str, Any], manifest_path: Path, verdict: str) -> None:
    fingerprint, expected = _manifest_commands(manifest_path)
    if payload.get("manifest_fingerprint") != fingerprint:
        raise GateVerificationError("proof payload manifest fingerprint is stale")
    executions = payload.get("executions")
    if not isinstance(executions, list):
        raise GateVerificationError("proof payload executions must be a list")
    if not isinstance(payload.get("absents"), list) or not all(
        isinstance(item, str) for item in payload["absents"]
    ):
        raise GateVerificationError("proof payload absents must be a string list")
    actual: dict[str, dict[str, Any]] = {}
    for execution in executions:
        if not isinstance(execution, dict) or not isinstance(execution.get("name"), str):
            raise GateVerificationError("invalid proof execution entry")
        name = execution["name"]
        if name in actual:
            raise GateVerificationError(f"duplicate proof execution: {name}")
        actual[name] = execution
    if set(actual) != set(expected):
        raise GateVerificationError("proof contains invented or missing commands")
    for name, command in expected.items():
        execution = actual[name]
        if execution.get("command") != command:
            raise GateVerificationError(f"proof command differs from manifest: {name}")
        if execution.get("status") not in {"passed", "failed", "not_run"}:
            raise GateVerificationError(f"invalid proof command status: {name}")
        exit_code = execution.get("exit_code")
        if exit_code is not None and (not isinstance(exit_code, int) or isinstance(exit_code, bool)):
            raise GateVerificationError(f"invalid proof command exit code: {name}")
        if verdict == "PASS" and (
            execution.get("status") != "passed" or execution.get("exit_code") != 0
        ):
            raise GateVerificationError(f"PASS gate contains non-passing command: {name}")


def _verify_head_correspondence(
    root: Path,
    head_sha: str,
    gate_relative: str,
    proof_relative: str,
) -> None:
    current = _git(root, "rev-parse", "HEAD").stdout.decode().strip()
    if current == head_sha:
        return
    ancestor = _git(root, "merge-base", "--is-ancestor", head_sha, current, check=False)
    if ancestor.returncode != 0:
        raise GateVerificationError("head_sha is not an ancestor of the current commit")
    changed = {
        line
        for line in _git(root, "diff", "--name-only", f"{head_sha}..{current}").stdout.decode().splitlines()
        if line
    }
    allowed = {gate_relative, proof_relative, "CHANGELOG.md"}
    unexpected = changed - allowed
    if unexpected:
        raise GateVerificationError(
            f"current commit has non-evidence changes after head_sha: {sorted(unexpected)}"
        )


def verify_gate(root: Path, gate_path: Path) -> dict[str, Any]:
    root = root.resolve()
    gate_path = gate_path.resolve()
    try:
        gate_relative = gate_path.relative_to(root).as_posix()
    except ValueError as error:
        raise GateVerificationError("gate path is outside repository") from error
    if not gate_relative.startswith("docs/quality/GATE-") or gate_path.suffix != ".yaml":
        raise GateVerificationError("gate must be docs/quality/GATE-*.yaml")
    content_bytes = gate_path.read_bytes()
    content = content_bytes.decode("utf-8")
    _verify_closed_gate_shape(content)
    expected_integrity = _scalar(content, "integrity_sha256")
    actual_integrity = hashlib.sha256(_normalized_gate_bytes(content_bytes)).hexdigest()
    if expected_integrity != actual_integrity:
        raise GateVerificationError("gate integrity hash mismatch")

    schema = _scalar(content, "schema_version")
    verdict = _scalar(content, "verdict")
    level = _scalar(content, "level")
    base_sha = _scalar(content, "base_sha")
    head_sha = _scalar(content, "head_sha")
    code_diff_hash = _scalar(content, "code_diff_hash")
    exclusions = _scalar(content, "code_diff_exclusions")
    proof_relative = _scalar(content, "proof_payload")
    proof_payload_hash = _scalar(content, "proof_payload_hash")
    if schema != SCHEMA_VERSION:
        raise GateVerificationError(f"unsupported gate schema: {schema}")
    if verdict not in {"PASS", "CONCERNS", "FAIL", "WAIVED"}:
        raise GateVerificationError(f"invalid gate verdict: {verdict}")
    if not isinstance(level, int) or isinstance(level, bool) or level not in {1, 2, 3, 4}:
        raise GateVerificationError("level must be an integer from 1 to 4")
    if not isinstance(base_sha, str) or not SHA_RE.fullmatch(base_sha):
        raise GateVerificationError("base_sha must be a full Git SHA")
    if not isinstance(head_sha, str) or not SHA_RE.fullmatch(head_sha):
        raise GateVerificationError("head_sha must be a full Git SHA")
    if not isinstance(code_diff_hash, str) or not HASH_RE.fullmatch(code_diff_hash):
        raise GateVerificationError("code_diff_hash must be SHA-256")
    if not isinstance(proof_payload_hash, str) or not HASH_RE.fullmatch(proof_payload_hash):
        raise GateVerificationError("proof_payload_hash must be SHA-256")
    if not isinstance(exclusions, list) or not all(isinstance(item, str) for item in exclusions):
        raise GateVerificationError("code_diff_exclusions must be a JSON-style string list")
    if len(exclusions) != len(set(exclusions)):
        raise GateVerificationError("code_diff_exclusions must be unique")
    if not isinstance(proof_relative, str):
        raise GateVerificationError("proof_payload must be a path")

    _git(root, "cat-file", "-e", f"{base_sha}^{{commit}}")
    _git(root, "cat-file", "-e", f"{head_sha}^{{commit}}")
    if _git(root, "merge-base", "--is-ancestor", base_sha, head_sha, check=False).returncode != 0:
        raise GateVerificationError("base_sha is not an ancestor of head_sha")
    if compute_code_diff_hash(root, base_sha, head_sha, exclusions) != code_diff_hash:
        raise GateVerificationError("code diff hash mismatch")

    proof_path = _safe_relative(root, proof_relative, "docs/quality/proofs/")
    if not proof_path.is_file():
        raise GateVerificationError("proof payload is missing")
    if hashlib.sha256(proof_path.read_bytes()).hexdigest() != proof_payload_hash:
        raise GateVerificationError("proof payload hash mismatch")
    payload = _load_unique_json(proof_path)
    if payload.get("schema_version") != PROOF_SCHEMA_VERSION:
        raise GateVerificationError("unsupported proof payload schema")
    _verify_executions(payload, root / ".agents" / "verification.yaml", verdict)
    _verify_head_correspondence(root, head_sha, gate_relative, proof_relative)
    tracked = set(_git(root, "ls-files", gate_relative, proof_relative).stdout.decode().splitlines())
    if tracked != {gate_relative, proof_relative}:
        raise GateVerificationError("gate and proof payload must be tracked by Git")
    if _git(root, "diff", "--quiet", "HEAD", "--", gate_relative, proof_relative, check=False).returncode != 0:
        raise GateVerificationError("gate or proof payload has uncommitted evidence changes")
    return {
        "status": "valid",
        "verdict": verdict,
        "base_sha": base_sha,
        "head_sha": head_sha,
        "current_sha": _git(root, "rev-parse", "HEAD").stdout.decode().strip(),
        "code_diff_hash": code_diff_hash,
        "proof_payload_hash": proof_payload_hash,
        "integrity_sha256": actual_integrity,
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("seal", "verify"))
    parser.add_argument("gate", type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    try:
        if args.action == "seal":
            print(json.dumps({"status": "sealed", "integrity_sha256": seal_gate(args.gate)}))
        else:
            print(json.dumps(verify_gate(args.root, args.gate), sort_keys=True))
    except (GateVerificationError, OSError, subprocess.CalledProcessError) as error:
        print(f"gate verification failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
