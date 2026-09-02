#!/usr/bin/env python3
"""Isolated behavioral case runner with generic filesystem and output assertions."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
import time
from typing import Any, Iterable


DANGEROUS_BYPASSES = {
    "--full-auto",
    "--dangerously-skip-permissions",
    "--dangerously-bypass-approvals-and-sandbox",
    "--yolo",
    "danger-full-access",
    "approval_policy=never",
}
MAX_CAPTURE_CHARS = 20_000


class HarnessError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _hash_tree(root: Path) -> tuple[str, dict[str, str]]:
    digest = hashlib.sha256()
    files: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            relative = path.relative_to(root).as_posix()
            value = f"symlink:{path.readlink().as_posix()}"
        elif path.is_file():
            relative = path.relative_to(root).as_posix()
            value = hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            continue
        files[relative] = value
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(value.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest(), files


def _fixture_path(case: dict[str, Any], repo_root: Path) -> Path:
    value = case.get("fixture")
    if not isinstance(value, str) or not value:
        raise HarnessError(f"case fixture is invalid: {case.get('id')}")
    candidate = Path(value)
    path = candidate if candidate.is_absolute() else repo_root / "behavioral" / "fixtures" / candidate
    path = path.resolve()
    if path.is_symlink() or not path.is_dir():
        raise HarnessError(f"case fixture is missing: {value}")
    if any(candidate.is_symlink() for candidate in path.rglob("*")):
        raise HarnessError(f"case fixture contains a symlink: {value}")
    return path


def _workspace_path(workspace: Path, value: Any) -> Path:
    relative = PurePosixPath(str(value))
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise HarnessError(f"unsafe assertion path: {value}")
    return workspace.joinpath(*relative.parts)


def _command(case: dict[str, Any], repo_root: Path, workspace: Path) -> list[str]:
    runner = case.get("runner")
    if not isinstance(runner, dict) or runner.get("type") != "command":
        raise HarnessError(f"unsupported runner for case: {case.get('id')}")
    raw = runner.get("command")
    if not isinstance(raw, list) or not raw or not all(isinstance(item, str) for item in raw):
        raise HarnessError(f"runner command is invalid: {case.get('id')}")
    command = [
        item.replace("{repo}", str(repo_root)).replace("{workspace}", str(workspace))
        for item in raw
    ]
    for argument in command:
        if any(token in argument for token in DANGEROUS_BYPASSES):
            raise HarnessError(f"permission bypass flag is forbidden: {argument}")
    return command


def _runtime_version(command: list[str]) -> str:
    try:
        completed = subprocess.run(
            [command[0], "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return Path(command[0]).name
    output = completed.stdout.strip() or completed.stderr.strip()
    return output.splitlines()[0] if completed.returncode == 0 and output else Path(command[0]).name


def _bounded(value: str) -> tuple[str, bool]:
    if len(value) <= MAX_CAPTURE_CHARS:
        return value, False
    return value[:MAX_CAPTURE_CHARS], True


def _assertion(kind: str, target: str, passed: bool, detail: str = "") -> dict[str, Any]:
    return {"kind": kind, "target": target, "passed": passed, "detail": detail}


def _ordered_subsequence(expected: list[str], actual: list[str]) -> bool:
    position = 0
    for item in actual:
        if position < len(expected) and item == expected[position]:
            position += 1
    return position == len(expected)


def _evaluate(
    expect: dict[str, Any],
    workspace: Path,
    stdout: str,
    events: list[str],
    before_files: dict[str, str],
    exit_code: int,
) -> list[dict[str, Any]]:
    expected_exit = expect.get("exit_code", 0)
    if not isinstance(expected_exit, int) or isinstance(expected_exit, bool):
        raise HarnessError("expected exit_code must be an integer")
    assertions = [
        _assertion("exit_code", str(expected_exit), exit_code == expected_exit, f"actual={exit_code}")
    ]
    expected_events = expect.get("events_in_order", [])
    if isinstance(expected_events, list):
        assertions.append(
            _assertion(
                "events_in_order",
                ",".join(str(item) for item in expected_events),
                _ordered_subsequence([str(item) for item in expected_events], events),
                f"actual={events}",
            )
        )
    for relative in expect.get("files_exist", []):
        path = _workspace_path(workspace, relative)
        assertions.append(_assertion("files_exist", str(relative), path.is_file() and not path.is_symlink()))
    for relative in expect.get("files_absent", []):
        path = _workspace_path(workspace, relative)
        assertions.append(_assertion("files_absent", str(relative), not path.exists() and not path.is_symlink()))
    for relative in expect.get("files_unchanged", []):
        relative_text = str(relative)
        path = _workspace_path(workspace, relative_text)
        current = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() and not path.is_symlink() else None
        assertions.append(
            _assertion(
                "files_unchanged",
                relative_text,
                before_files.get(relative_text) is not None and current == before_files.get(relative_text),
            )
        )
    for relative, needles in expect.get("file_contains", {}).items():
        path = _workspace_path(workspace, relative)
        content = path.read_text(encoding="utf-8") if path.is_file() and not path.is_symlink() else ""
        for needle in needles:
            assertions.append(_assertion("file_contains", f"{relative}:{needle}", str(needle) in content))
    for relative, patterns in expect.get("file_matches", {}).items():
        path = _workspace_path(workspace, relative)
        content = path.read_text(encoding="utf-8") if path.is_file() and not path.is_symlink() else ""
        for pattern in patterns:
            assertions.append(
                _assertion(
                    "file_matches",
                    f"{relative}:{pattern}",
                    re.search(str(pattern), content, re.MULTILINE) is not None,
                )
            )
    for needle in expect.get("stdout_contains", []):
        assertions.append(_assertion("stdout_contains", str(needle), str(needle) in stdout))
    return assertions


def run_case(
    case: dict[str, Any],
    *,
    repo_root: Path,
    base_sha: str,
    head_sha: str,
    iteration: int,
    failure_root: Path | None = None,
) -> dict[str, Any]:
    identifier = case.get("id")
    if not isinstance(identifier, str) or not identifier:
        raise HarnessError("case id is invalid")
    if re.fullmatch(r"[a-z0-9][a-z0-9-]*", identifier) is None:
        raise HarnessError(f"case id is unsafe: {identifier}")
    if re.fullmatch(r"[0-9a-f]{40}", base_sha) is None or re.fullmatch(
        r"[0-9a-f]{40}", head_sha
    ) is None:
        raise HarnessError("base_sha and head_sha must be full Git SHAs")
    if case.get("permissions") != "workspace_fixture_only":
        raise HarnessError(f"unsupported permissions for case: {identifier}")
    timeout = case.get("timeout_seconds")
    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout <= 0:
        raise HarnessError(f"case timeout is invalid: {identifier}")
    repo_root = Path(repo_root).resolve()
    fixture = _fixture_path(case, repo_root)
    started_at = _now()
    with tempfile.TemporaryDirectory(prefix=f"skillz-eval-{identifier}-") as temporary:
        workspace = Path(temporary) / "workspace"
        shutil.copytree(fixture, workspace, symlinks=True)
        before_hash, before_files = _hash_tree(workspace)
        command = _command(case, repo_root, workspace)
        environment = dict(os.environ)
        environment["SKILLZ_CASE_INPUT"] = str(case.get("input", ""))
        start = time.monotonic()
        try:
            completed = subprocess.run(
                command,
                cwd=workspace,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
                check=False,
            )
            exit_code = completed.returncode
            stdout = completed.stdout
            stderr = completed.stderr
        except subprocess.TimeoutExpired as error:
            exit_code = 124
            stdout = error.stdout.decode() if isinstance(error.stdout, bytes) else error.stdout or ""
            stderr = error.stderr.decode() if isinstance(error.stderr, bytes) else error.stderr or ""
        except OSError as error:
            exit_code = 127
            stdout = ""
            stderr = str(error)
        duration_ms = round((time.monotonic() - start) * 1000)
        events = re.findall(r"(?m)^EVENT:([A-Za-z0-9_-]+)\s*$", stdout)
        expect = case.get("expect") if isinstance(case.get("expect"), dict) else {}
        assertions = _evaluate(expect, workspace, stdout, events, before_files, exit_code)
        after_hash, after_files = _hash_tree(workspace)
        status = "passed" if all(item["passed"] for item in assertions) else "failed"
        captured_stdout, stdout_truncated = _bounded(stdout)
        captured_stderr, stderr_truncated = _bounded(stderr)
        preserved_workspace = None
        if status == "failed" and failure_root is not None:
            destination = Path(failure_root) / f"{identifier}-run-{iteration}"
            if destination.exists() or destination.is_symlink():
                raise HarnessError(f"failure workspace already exists: {destination}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(workspace, destination, symlinks=True)
            preserved_workspace = str(destination.resolve())
        return {
            "schema_version": 1,
            "case_id": identifier,
            "iteration": iteration,
            "runtime": case.get("runtime"),
            "runtime_version": _runtime_version(command),
            "model": case.get("model"),
            "seed": case.get("seed"),
            "base_sha": base_sha,
            "head_sha": head_sha,
            "started_at": started_at,
            "duration_ms": duration_ms,
            "exit_code": exit_code,
            "status": status,
            "events": events,
            "stdout": captured_stdout,
            "stderr": captured_stderr,
            "stdout_truncated": stdout_truncated,
            "stderr_truncated": stderr_truncated,
            "hashes_before": before_hash,
            "hashes_after": after_hash,
            "changed_files": sorted(
                path for path in set(before_files) | set(after_files) if before_files.get(path) != after_files.get(path)
            ),
            "assertions": assertions,
            "preserved_workspace": preserved_workspace,
            "certification_claim": "C1" if case.get("runtime") == "fixture" else "none",
        }


def run_suite(
    cases: list[dict[str, Any]],
    *,
    repo_root: Path,
    base_sha: str,
    head_sha: str,
    repeat: int | None = None,
    jobs: int = 1,
    failure_root: Path | None = None,
) -> dict[str, Any]:
    if (repeat is not None and repeat <= 0) or jobs <= 0:
        raise HarnessError("repeat and jobs must be positive")
    tasks: list[tuple[dict[str, Any], int]] = []
    for case in cases:
        case_repeat = repeat if repeat is not None else case.get("repeat", 1)
        if not isinstance(case_repeat, int) or isinstance(case_repeat, bool) or case_repeat <= 0:
            raise HarnessError(f"case repeat is invalid: {case.get('id')}")
        tasks.extend((case, iteration) for iteration in range(1, case_repeat + 1))
    with ThreadPoolExecutor(max_workers=jobs) as executor:
        futures = [
            executor.submit(
                run_case,
                case,
                repo_root=repo_root,
                base_sha=base_sha,
                head_sha=head_sha,
                iteration=iteration,
                failure_root=failure_root,
            )
            for case, iteration in tasks
        ]
        results = [future.result() for future in futures]
    results.sort(key=lambda item: (item["case_id"], item["iteration"]))
    passed = sum(item["status"] == "passed" for item in results)
    return {
        "schema_version": 1,
        "generated_at": _now(),
        "base_sha": base_sha,
        "head_sha": head_sha,
        "summary": {"passed": passed, "failed": len(results) - passed, "total": len(results)},
        "results": results,
    }


def load_cases(directory: Path, selected: set[str] | None = None) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for path in sorted(Path(directory).glob("*.yaml")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise HarnessError(f"invalid case file: {path}: {error}") from error
        if not isinstance(payload, dict):
            raise HarnessError(f"case must be an object: {path}")
        if selected is None or payload.get("id") in selected:
            cases.append(payload)
    if not cases:
        raise HarnessError("no behavioral cases selected")
    identifiers = [case.get("id") for case in cases]
    if len(identifiers) != len(set(identifiers)):
        raise HarnessError("duplicate behavioral case ids")
    return cases


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=Path("behavioral/cases"))
    parser.add_argument("--case", action="append", dest="selected")
    parser.add_argument("--repeat", type=int)
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--failure-dir", type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    try:
        report = run_suite(
            load_cases(args.cases, set(args.selected) if args.selected else None),
            repo_root=args.root,
            base_sha=args.base_sha,
            head_sha=args.head_sha,
            repeat=args.repeat,
            jobs=args.jobs,
            failure_root=args.failure_dir,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(report["summary"], sort_keys=True))
        return 0 if report["summary"]["failed"] == 0 else 1
    except (HarnessError, OSError) as error:
        print(f"behavioral harness failed: {error}", file=__import__("sys").stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
