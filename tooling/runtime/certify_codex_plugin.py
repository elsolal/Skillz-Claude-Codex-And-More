#!/usr/bin/env python3
"""Certify a generated Codex plugin in an isolated Codex home."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Iterable


MINIMUM_PYTHON = (3, 10)


class CertificationError(RuntimeError):
    pass


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CertificationError(f"invalid {label}: {path}: {error}") from error
    if not isinstance(payload, dict):
        raise CertificationError(f"{label} must be a JSON object: {path}")
    return payload


def _run_json(command: list[str], environment: dict[str, str]) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise CertificationError(f"command failed ({completed.returncode}): {' '.join(command)}: {detail}")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise CertificationError(f"command returned invalid JSON: {' '.join(command)}") from error
    if not isinstance(payload, dict):
        raise CertificationError(f"command returned a non-object: {' '.join(command)}")
    return payload


def _find_plugin(payload: dict[str, Any], collection: str, plugin_id: str) -> dict[str, Any]:
    entries = payload.get(collection)
    if not isinstance(entries, list):
        raise CertificationError(f"Codex response has no {collection} list")
    for entry in entries:
        if isinstance(entry, dict) and entry.get("pluginId") == plugin_id:
            return entry
    raise CertificationError(f"plugin not found in {collection}: {plugin_id}")


def certify(bundle: Path, codex_binary: str) -> dict[str, Any]:
    if sys.version_info[:2] < MINIMUM_PYTHON:
        raise CertificationError("Python 3.10 or newer is required")
    resolved_binary = shutil.which(codex_binary)
    if resolved_binary is None:
        raise CertificationError(f"Codex binary not found: {codex_binary}")
    bundle = bundle.resolve()
    manifest_path = bundle / ".codex-plugin" / "plugin.json"
    marketplace_path = bundle / ".agents" / "plugins" / "marketplace.json"
    manifest = _load_json(manifest_path, "Codex plugin manifest")
    marketplace = _load_json(marketplace_path, "Codex marketplace manifest")
    plugin_name = manifest.get("name")
    version = manifest.get("version")
    marketplace_name = marketplace.get("name")
    if not all(isinstance(value, str) and value for value in (plugin_name, version, marketplace_name)):
        raise CertificationError("plugin and marketplace identities must be non-empty strings")
    plugins = marketplace.get("plugins")
    if (
        not isinstance(plugins, list)
        or len(plugins) != 1
        or not isinstance(plugins[0], dict)
        or plugins[0].get("name") != plugin_name
    ):
        raise CertificationError("marketplace must expose exactly the generated plugin")
    plugin_id = f"{plugin_name}@{marketplace_name}"

    version_result = subprocess.run(
        [resolved_binary, "--version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if version_result.returncode != 0 or not version_result.stdout.strip():
        raise CertificationError("Codex version command failed")
    runtime_version = version_result.stdout.strip()

    with tempfile.TemporaryDirectory(prefix="skillz-codex-cert-") as isolated_home:
        environment = dict(os.environ)
        environment["CODEX_HOME"] = isolated_home
        added_marketplace = _run_json(
            [resolved_binary, "plugin", "marketplace", "add", str(bundle), "--json"],
            environment,
        )
        if added_marketplace.get("marketplaceName") != marketplace_name:
            raise CertificationError("Codex registered the wrong marketplace")
        listed_marketplaces = _run_json(
            [resolved_binary, "plugin", "marketplace", "list", "--json"],
            environment,
        )
        marketplace_entries = listed_marketplaces.get("marketplaces")
        if not isinstance(marketplace_entries, list) or not any(
            isinstance(item, dict) and item.get("name") == marketplace_name
            for item in marketplace_entries
        ):
            raise CertificationError("registered marketplace is not listed")
        available_payload = _run_json(
            [resolved_binary, "plugin", "list", "--available", "--json"],
            environment,
        )
        available = _find_plugin(available_payload, "available", plugin_id)
        if available.get("version") != version or available.get("installed") is not False:
            raise CertificationError("available plugin metadata does not match the manifest")
        installed_result = _run_json(
            [resolved_binary, "plugin", "add", plugin_id, "--json"],
            environment,
        )
        installed_path_value = installed_result.get("installedPath")
        if installed_result.get("pluginId") != plugin_id or not isinstance(installed_path_value, str):
            raise CertificationError("Codex did not return a valid installed plugin")
        installed_path = Path(installed_path_value)
        try:
            installed_path.resolve().relative_to(Path(isolated_home).resolve())
        except ValueError as error:
            raise CertificationError("Codex installed the plugin outside the isolated home") from error
        installed_payload = _run_json(
            [resolved_binary, "plugin", "list", "--json"],
            environment,
        )
        installed = _find_plugin(installed_payload, "installed", plugin_id)
        if installed.get("installed") is not True or installed.get("enabled") is not True:
            raise CertificationError("installed plugin is not enabled")
        expected_skills = ("dev-workflow", "project-probe", "quality-gate", "status-workflow")
        missing_skills = [
            skill
            for skill in expected_skills
            if not (installed_path / "skills" / skill / "SKILL.md").is_file()
        ]
        if missing_skills:
            raise CertificationError(f"installed plugin is missing skills: {missing_skills}")

    return {
        "schema_version": 1,
        "provider": "codex",
        "certification": "C2",
        "runtime": runtime_version,
        "plugin": {
            "id": plugin_id,
            "version": version,
            "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            "marketplace_sha256": hashlib.sha256(marketplace_path.read_bytes()).hexdigest(),
        },
        "checks": {
            "marketplace_registered": True,
            "marketplace_listed": True,
            "plugin_available": True,
            "plugin_installed": True,
            "plugin_enabled": True,
            "installed_vertical_slice_skills": 4,
        },
        "isolation": "temporary CODEX_HOME; user configuration unchanged",
        "limitations": [
            "C2 proves native discovery and installation, not behavioral invocation",
            "headless skill invocation, hooks and alternate model providers remain pending",
        ],
    }


def _render(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=Path("dist/codex"))
    parser.add_argument("--codex", default="codex")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        rendered = _render(certify(args.bundle, args.codex))
        if args.check:
            if not args.output.is_file() or args.output.read_text(encoding="utf-8") != rendered:
                raise CertificationError(f"Codex certification evidence is stale: {args.output}")
            print(f"Codex plugin certification is fresh: {args.output}")
            return 0
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"wrote {args.output}")
        return 0
    except (CertificationError, OSError) as error:
        print(f"Codex plugin certification failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
