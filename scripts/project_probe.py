#!/usr/bin/env python3
"""Deterministic, read-only collector for .agents/verification.yaml."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Iterable


PROBE_VERSION = "2.0.0"
FINGERPRINT_SCHEMA_VERSION = 2
MINIMUM_PYTHON = (3, 10)
EXCLUDED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "vendor",
}
CONFIG_NAMES = {
    ".python-version",
    "Cargo.lock",
    "Cargo.toml",
    "Dockerfile",
    "Gemfile",
    "Gemfile.lock",
    "Makefile",
    "biome.json",
    "composer.json",
    "composer.lock",
    "go.mod",
    "go.sum",
    "justfile",
    "package-lock.json",
    "package.json",
    "pnpm-lock.yaml",
    "pnpm-workspace.yaml",
    "project-probe.json",
    "project_probe.py",
    "pyproject.toml",
    "pytest.ini",
    "requirements.txt",
    "setup.cfg",
    "tox.ini",
    "turbo.json",
    "yarn.lock",
}
PROVIDER_ROOTS = {
    ".agents",
    ".claude-plugin",
    ".codex",
    ".gemini",
    ".opencode",
    "providers",
}
PROVIDER_SUFFIXES = {".json", ".md", ".toml", ".yaml", ".yml"}
SHELL_ROLES = {
    "build": "build",
    "check": "lint",
    "lint": "lint",
    "test": "test",
    "verify": "test",
}
UNSAFE_SHELL = re.compile(
    r"(?:\brm\s+-[^\n]*(?:r|f)|\bcurl\b|\bwget\b|\bgit\s+push\b|"
    r"\b(?:npm|pnpm|yarn)\s+publish\b|\bdeploy\b|\bdestroy\b|"
    r"\bdb(?::|\s+)reset\b|\bdrop\s+database\b)",
    re.IGNORECASE,
)


def require_supported_python(version: tuple[int, ...] | None = None) -> None:
    detected = tuple(version or sys.version_info[:3])
    if detected[:2] < MINIMUM_PYTHON:
        rendered = ".".join(str(part) for part in detected[:2])
        raise RuntimeError(f"Python 3.10 or newer is required; detected {rendered}")


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _is_fingerprint_source(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    parts = relative.parts
    if any(part in EXCLUDED_PARTS for part in parts):
        return False
    relative_text = relative.as_posix()
    if relative_text == ".agents/verification.yaml":
        return False
    if path.name in CONFIG_NAMES or path.suffix == ".sh" or path.name == "SKILL.md":
        return True
    if parts and parts[0] == "scripts" and path.suffix == ".py":
        return True
    if parts[:2] == (".github", "workflows") and path.suffix in {".yml", ".yaml"}:
        return True
    if parts and parts[0] in PROVIDER_ROOTS and path.suffix in PROVIDER_SUFFIXES:
        return True
    if len(parts) >= 2 and parts[0] in {"core", "tooling"} and path.suffix in PROVIDER_SUFFIXES:
        return True
    if len(parts) >= 2 and parts[:2] == (".claude", "commands") and path.suffix == ".md":
        return True
    return False


def _candidate_paths(root: Path) -> list[Path]:
    if (root / ".git").exists():
        completed = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=root,
            check=True,
            stdout=subprocess.PIPE,
        )
        return [
            root / relative
            for relative in completed.stdout.decode("utf-8").split("\0")
            if relative
        ]
    return list(root.rglob("*"))


def fingerprint_sources(root: Path) -> list[str]:
    root = root.resolve()
    sources: list[str] = []
    for candidate in _candidate_paths(root):
        if not (candidate.is_file() or candidate.is_symlink()):
            continue
        if _is_fingerprint_source(candidate, root):
            sources.append(_relative(candidate, root))
    return sorted(set(sources))


def compute_fingerprint(root: Path) -> dict[str, Any]:
    root = root.resolve()
    sources = fingerprint_sources(root)
    digest = hashlib.sha256()
    for relative_path in sources:
        source = root / relative_path
        content = source.readlink().as_posix().encode("utf-8") if source.is_symlink() else source.read_bytes()
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(content)
        digest.update(b"\0")
    return {"sha256": digest.hexdigest(), "sources": sources}


def is_safe_shell_candidate(content: str) -> bool:
    return not bool(UNSAFE_SHELL.search(content))


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _package_manager(root: Path) -> str:
    if (root / "pnpm-lock.yaml").exists() or (root / "pnpm-workspace.yaml").exists():
        return "pnpm"
    if (root / "yarn.lock").exists():
        return "yarn"
    return "npm"


def _node_command(manager: str, script_name: str) -> str:
    if script_name == "test":
        return f"{manager} test"
    return f"{manager} run {script_name}"


def _node_signals(root: Path) -> tuple[dict[str, str], dict[str, str], dict[str, Any]]:
    package_path = root / "package.json"
    if not package_path.is_file():
        return {}, {}, {}
    try:
        package = json.loads(package_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, {}, {}
    scripts = package.get("scripts", {}) if isinstance(package.get("scripts", {}), dict) else {}
    manager = _package_manager(root)
    aliases = {
        "build": ("build",),
        "lint": ("lint", "check"),
        "test": ("test", "test:unit"),
        "typecheck": ("typecheck", "type-check"),
    }
    commands: dict[str, str] = {}
    sources: dict[str, str] = {}
    for role, names in aliases.items():
        for name in names:
            value = scripts.get(name)
            if isinstance(value, str) and is_safe_shell_candidate(value):
                commands[role] = _node_command(manager, name)
                sources[role] = f"package.json#scripts.{name}"
                break
    monorepo: dict[str, Any] = {}
    workspaces = package.get("workspaces")
    if isinstance(workspaces, dict):
        workspaces = workspaces.get("packages")
    if isinstance(workspaces, list) or (root / "pnpm-workspace.yaml").exists():
        monorepo = {"manager": manager, "workspaces": workspaces or _pnpm_workspaces(root)}
    return commands, sources, monorepo


def _pnpm_workspaces(root: Path) -> list[str]:
    content = _read_text(root / "pnpm-workspace.yaml")
    return re.findall(r"^\s*-\s*['\"]?([^'\"\n]+)", content, re.MULTILINE)


def _python_required(root: Path) -> str:
    content = _read_text(root / "pyproject.toml")
    match = re.search(r'^requires-python\s*=\s*["\']([^"\']+)', content, re.MULTILINE)
    if match:
        return match.group(1)
    version_file = _read_text(root / ".python-version").strip()
    return f">={version_file}" if version_file else ">=3.10"


def _python_signals(root: Path) -> tuple[dict[str, str], dict[str, str]]:
    pyproject = root / "pyproject.toml"
    setup_cfg = root / "setup.cfg"
    if not pyproject.is_file() and not setup_cfg.is_file():
        return {}, {}
    pyproject_content = _read_text(pyproject).lower()
    setup_content = _read_text(setup_cfg).lower()
    content = pyproject_content + "\n" + setup_content
    config_name = "pyproject.toml" if pyproject.is_file() else "setup.cfg"
    commands: dict[str, str] = {}
    sources: dict[str, str] = {}
    if "ruff" in content:
        commands["lint"] = "python -m ruff check ."
        section = "tool.ruff" if "[tool.ruff" in pyproject_content else "dependency.ruff"
        sources["lint"] = f"{config_name}#{section}"
    if "mypy" in content:
        commands["typecheck"] = "python -m mypy ."
        section = "tool.mypy" if "[tool.mypy" in pyproject_content else "dependency.mypy"
        sources["typecheck"] = f"{config_name}#{section}"
    if "pytest" in content:
        commands["test"] = "python -m pytest"
        section = "tool.pytest" if "[tool.pytest" in pyproject_content else "dependency.pytest"
        sources["test"] = f"{config_name}#{section}"
    return commands, sources


def _shell_signals(root: Path) -> tuple[dict[str, str], dict[str, str]]:
    commands: dict[str, str] = {}
    sources: dict[str, str] = {}
    for relative_dir in (Path("scripts"), Path("tests"), Path(".")):
        directory = root / relative_dir
        if not directory.is_dir():
            continue
        for script in sorted(directory.glob("*.sh")):
            role = SHELL_ROLES.get(script.stem)
            if not role or role in commands:
                continue
            if not is_safe_shell_candidate(_read_text(script)):
                continue
            relative = _relative(script, root)
            commands[role] = f"bash {relative}"
            sources[role] = relative
    return commands, sources


def _merge_missing(primary: dict[str, str], fallback: dict[str, str]) -> dict[str, str]:
    merged = dict(primary)
    for key, value in fallback.items():
        merged.setdefault(key, value)
    return dict(sorted(merged.items()))


def _load_overrides(root: Path) -> dict[str, Any]:
    config_path = root / ".agents" / "project-probe.json"
    if not config_path.is_file():
        return {}
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) and payload.get("schema_version") == 1 else {}


def _override_commands(overrides: dict[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    declared = overrides.get("commands", {})
    if not isinstance(declared, dict):
        return {}, {}
    commands: dict[str, str] = {}
    sources: dict[str, str] = {}
    for role in ("build", "lint", "test", "typecheck"):
        command = declared.get(role)
        if isinstance(command, str) and is_safe_shell_candidate(command):
            commands[role] = command
            sources[role] = f".agents/project-probe.json#commands.{role}"
    return commands, sources


def _stack(root: Path) -> str:
    markers = []
    if (root / "package.json").exists():
        markers.append("node-js")
    if (root / "pyproject.toml").exists() or (root / "setup.cfg").exists():
        markers.append("python")
    if (root / "Cargo.toml").exists():
        markers.append("rust")
    if (root / "go.mod").exists():
        markers.append("go")
    if len(markers) > 1:
        return "mixed"
    if markers:
        return markers[0]
    if any(root.rglob("*.sh")):
        return "shell"
    return "unknown"


def _testability(root: Path, commands: dict[str, str]) -> dict[str, str]:
    combined = "\n".join(_read_text(root / name).lower() for name in ("package.json", "pyproject.toml", "setup.cfg"))
    harness = next((name for name in ("vitest", "jest", "pytest") if name in combined), "none")
    e2e = next((name for name in ("playwright", "cypress") if name in combined), "none")
    return {"harness": harness, "e2e": e2e, "runtime_verify": "none"}


def probe_project(root: Path) -> dict[str, Any]:
    require_supported_python()
    root = root.resolve()
    fingerprint = compute_fingerprint(root)
    node_commands, node_sources, monorepo = _node_signals(root)
    python_commands, python_sources = _python_signals(root)
    shell_commands, shell_sources = _shell_signals(root)
    overrides = _load_overrides(root)
    override_commands, override_sources = _override_commands(overrides)
    commands = _merge_missing(override_commands, node_commands)
    commands = _merge_missing(commands, python_commands)
    commands = _merge_missing(commands, shell_commands)
    command_sources = _merge_missing(override_sources, node_sources)
    command_sources = _merge_missing(command_sources, python_sources)
    command_sources = _merge_missing(command_sources, shell_sources)
    capabilities = ("lint", "typecheck", "test", "build")
    declared_absences = overrides.get("absence_reasons", {})
    if not isinstance(declared_absences, dict):
        declared_absences = {}
    absence_reasons = {
        capability: f"no safe {capability} command found in consumed project configuration"
        for capability in capabilities
        if capability not in commands
    }
    absence_reasons.update(
        {
            str(capability): str(reason)
            for capability, reason in declared_absences.items()
            if capability not in commands
        }
    )
    has_python = (root / "pyproject.toml").exists() or (root / "setup.cfg").exists()
    python_required = overrides.get("python_required")
    if not isinstance(python_required, str):
        python_required = _python_required(root) if has_python else "collector >=3.10"
    stack = overrides.get("stack") if isinstance(overrides.get("stack"), str) else _stack(root)
    testability = _testability(root, commands)
    declared_testability = overrides.get("testability", {})
    if isinstance(declared_testability, dict):
        testability.update(
            {str(key): str(value) for key, value in declared_testability.items() if key in testability}
        )
    selected_python = Path(os.environ.get("SKILLZ_SELECTED_PYTHON", sys.executable)).name
    result: dict[str, Any] = {
        "fingerprint_schema_version": FINGERPRINT_SCHEMA_VERSION,
        "generated_by": f"project-probe/{PROBE_VERSION}",
        "stack": stack,
        "config_fingerprint": fingerprint["sha256"],
        "fingerprint_sources": fingerprint["sources"],
        "python": {
            "required": python_required,
            "selected_interpreter": selected_python,
            "selected_version": ".".join(str(part) for part in sys.version_info[:3]),
        },
        "commands": commands,
        "command_sources": command_sources,
        "testability": testability,
        "absents": list(absence_reasons.values()),
        "absence_reasons": absence_reasons,
    }
    if monorepo:
        result["monorepo"] = monorepo
    return result


def _quote(value: Any) -> str:
    if value == "none":
        return "none"
    return json.dumps(str(value), ensure_ascii=False)


def _mapping(lines: list[str], key: str, values: dict[str, Any], indent: int = 0) -> None:
    prefix = " " * indent
    lines.append(f"{prefix}{key}:")
    if not values:
        lines[-1] += " {}"
        return
    for child_key in sorted(values):
        child = values[child_key]
        if isinstance(child, list):
            lines.append(f"{prefix}  {child_key}:")
            lines.extend(f"{prefix}    - {_quote(item)}" for item in child)
        else:
            lines.append(f"{prefix}  {child_key}: {_quote(child)}")


def render_manifest(result: dict[str, Any]) -> str:
    lines = [
        "# .agents/verification.yaml — generated by project-probe. Committed.",
        f"fingerprint_schema_version: {result['fingerprint_schema_version']}",
        f"generated_by: {_quote(result['generated_by'])}",
        f"stack: {_quote(result['stack'])}",
        f"config_fingerprint: {_quote(result['config_fingerprint'])}",
    ]
    if result["fingerprint_sources"]:
        lines.append("fingerprint_sources:")
        lines.extend(f"  - {_quote(source)}" for source in result["fingerprint_sources"])
    else:
        lines.append("fingerprint_sources: []")
    _mapping(lines, "python", result["python"])
    _mapping(lines, "commands", result["commands"])
    _mapping(lines, "command_sources", result["command_sources"])
    _mapping(lines, "testability", result["testability"])
    lines.append("absents:")
    lines.extend(f"  - {_quote(reason)}" for reason in result["absents"])
    _mapping(lines, "absence_reasons", result["absence_reasons"])
    if "monorepo" in result:
        _mapping(lines, "monorepo", result["monorepo"])
    return "\n".join(lines) + "\n"


def manifest_is_fresh(output: Path, result: dict[str, Any]) -> bool:
    if not output.is_file():
        return False
    content = output.read_text(encoding="utf-8")
    schema = re.search(r"^fingerprint_schema_version:\s*(\d+)\s*$", content, re.MULTILINE)
    generator = re.search(r'^generated_by:\s*["\']?([^"\'\n]+)', content, re.MULTILINE)
    fingerprint = re.search(
        r'^config_fingerprint:\s*["\']?([0-9a-f]{64})',
        content,
        re.MULTILINE,
    )
    return bool(
        schema
        and int(schema.group(1)) == FINGERPRINT_SCHEMA_VERSION
        and generator
        and generator.group(1) == f"project-probe/{PROBE_VERSION}"
        and fingerprint
        and fingerprint.group(1) == result["config_fingerprint"]
    )


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--stdout", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = probe_project(args.root)
    except RuntimeError as error:
        parser.error(str(error))
    rendered = render_manifest(result)
    output = args.output or args.root / ".agents" / "verification.yaml"
    if args.check:
        if not manifest_is_fresh(output, result):
            print("verification manifest schema, generator, or fingerprint is stale", file=sys.stderr)
            return 1
        print(f"verification manifest is fresh ({result['config_fingerprint']})")
        return 0
    if args.stdout:
        print(rendered, end="")
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    print(f"selected Python: {Path(sys.executable).resolve()} ({result['python']['selected_version']})")
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
