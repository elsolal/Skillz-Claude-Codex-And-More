#!/usr/bin/env python3
"""Deterministic provider compiler for the Skillz neutral catalog."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile
from typing import Any, Iterable
import uuid


ARTIFACT_TYPES = ("instruction", "skill", "command", "agent", "mcp", "hook")
STATUSES = {"supported", "pending", "unsupported"}
CERTIFICATIONS = {"C0", "C1", "C2", "C3"}
PACKAGE_COMPONENTS = {"apps", "commands", "hooks", "mcpServers", "skills"}
PACKAGE_MANIFEST_FORMATS = {"distribution", "gemini-extension"}
TRANSFORM_TYPES = {
    "copy": set(ARTIFACT_TYPES),
    "gemini-command": {"command"},
}
ALIAS_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class BuildError(RuntimeError):
    pass


def _load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BuildError(f"invalid {label}: {path}: {error}") from error
    if not isinstance(payload, dict):
        raise BuildError(f"{label} must be an object: {path}")
    return payload


def _safe_relative(value: str, label: str) -> PurePosixPath:
    relative = PurePosixPath(value)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise BuildError(f"unsafe {label}: {value}")
    return relative


def _validate_distribution(catalog: dict[str, Any]) -> dict[str, Any]:
    distribution = catalog.get("distribution")
    if not isinstance(distribution, dict):
        raise BuildError("catalog distribution must be an object")
    required = {
        "name",
        "version",
        "description",
        "author",
        "homepage",
        "repository",
        "license",
        "keywords",
        "marketplace",
    }
    missing = required - set(distribution)
    if missing:
        raise BuildError(f"catalog distribution fields missing: {sorted(missing)}")
    if not isinstance(distribution.get("name"), str) or not ALIAS_RE.fullmatch(
        distribution["name"]
    ):
        raise BuildError("catalog distribution name is invalid")
    for field in ("version", "description", "homepage", "repository", "license"):
        if not isinstance(distribution.get(field), str) or not distribution[field]:
            raise BuildError(f"catalog distribution {field} is invalid")
    author = distribution.get("author")
    if not isinstance(author, dict) or not isinstance(author.get("name"), str):
        raise BuildError("catalog distribution author is invalid")
    keywords = distribution.get("keywords")
    if not isinstance(keywords, list) or not all(isinstance(item, str) for item in keywords):
        raise BuildError("catalog distribution keywords are invalid")
    marketplace = distribution.get("marketplace")
    marketplace_fields = {
        "name",
        "display_name",
        "category",
        "installation_policy",
        "authentication_policy",
    }
    if not isinstance(marketplace, dict) or marketplace_fields - set(marketplace):
        raise BuildError("catalog distribution marketplace is invalid")
    if not ALIAS_RE.fullmatch(str(marketplace.get("name", ""))):
        raise BuildError("catalog marketplace name is invalid")
    if marketplace.get("installation_policy") not in {"AVAILABLE", "REQUIRED"}:
        raise BuildError("catalog marketplace installation policy is invalid")
    if marketplace.get("authentication_policy") not in {"ON_INSTALL", "ON_USE"}:
        raise BuildError("catalog marketplace authentication policy is invalid")
    return distribution


def _validate_catalog(root: Path, catalog: dict[str, Any]) -> list[dict[str, Any]]:
    if catalog.get("schema_version") != 1 or not isinstance(catalog.get("artifacts"), list):
        raise BuildError("catalog must use schema_version 1 and contain artifacts")
    artifacts = catalog["artifacts"]
    identifiers: set[str] = set()
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            raise BuildError("catalog artifact must be an object")
        identifier = artifact.get("id")
        if not isinstance(identifier, str) or not ALIAS_RE.fullmatch(identifier):
            raise BuildError(f"invalid artifact id: {identifier}")
        if identifier in identifiers:
            raise BuildError(f"duplicate artifact id: {identifier}")
        identifiers.add(identifier)
        if artifact.get("type") not in ARTIFACT_TYPES:
            raise BuildError(f"invalid artifact type: {identifier}")
        required = {
            "id",
            "public_name",
            "type",
            "source",
            "dependencies",
            "inputs",
            "outputs",
            "aliases",
            "providers",
            "risk",
            "migration_state",
        }
        missing = required - set(artifact)
        if missing:
            raise BuildError(f"artifact fields missing for {identifier}: {sorted(missing)}")
        source_value = artifact.get("source")
        if not isinstance(source_value, str):
            raise BuildError(f"artifact source missing: {identifier}")
        source = root / _safe_relative(source_value, "artifact source")
        if source.is_symlink() or not source.is_file():
            raise BuildError(f"artifact source missing or non-regular: {source_value}")
        dependencies = artifact.get("dependencies")
        if not isinstance(dependencies, list) or not all(isinstance(item, str) for item in dependencies):
            raise BuildError(f"artifact dependencies invalid: {identifier}")
        providers = artifact.get("providers")
        if not isinstance(providers, list) or not all(isinstance(item, str) for item in providers):
            raise BuildError(f"artifact providers invalid: {identifier}")
        if artifact.get("migration_state") not in {"legacy", "canonical", "pending", "retired"}:
            raise BuildError(f"artifact migration_state invalid: {identifier}")
        risk = artifact.get("risk")
        if not isinstance(risk, int) or isinstance(risk, bool) or risk not in range(5):
            raise BuildError(f"artifact risk invalid: {identifier}")
        aliases = artifact.get("aliases")
        if not isinstance(aliases, dict) or not all(
            isinstance(key, str) and isinstance(value, str) for key, value in aliases.items()
        ):
            raise BuildError(f"artifact aliases invalid: {identifier}")
    for artifact in artifacts:
        for dependency in artifact["dependencies"]:
            if dependency not in identifiers:
                raise BuildError(f"missing dependency {dependency} for {artifact['id']}")
    return sorted(artifacts, key=lambda item: item["id"])


def _load_providers(root: Path) -> list[dict[str, Any]]:
    providers_root = root / "providers"
    providers: list[dict[str, Any]] = []
    for directory in sorted(path for path in providers_root.iterdir() if path.is_dir()):
        capabilities = _load_object(directory / "capabilities.yaml", "provider capabilities")
        contract = _load_object(directory / "build-contract.json", "provider build contract")
        provider = directory.name
        if capabilities.get("provider") != provider or contract.get("provider") != provider:
            raise BuildError(f"provider identity mismatch: {provider}")
        if capabilities.get("schema_version") != 1 or contract.get("schema_version") != 1:
            raise BuildError(f"unsupported provider schema: {provider}")
        certification = capabilities.get("certification")
        runtime = capabilities.get("runtime")
        if certification not in CERTIFICATIONS or not isinstance(runtime, dict):
            raise BuildError(f"invalid provider certification: {provider}")
        if not isinstance(runtime.get("name"), str) or not runtime["name"]:
            raise BuildError(f"provider runtime name missing: {provider}")
        version_observed = runtime.get("version_observed")
        if version_observed is not None and not isinstance(version_observed, str):
            raise BuildError(f"provider runtime version is invalid: {provider}")
        if certification in {"C2", "C3"} and not version_observed:
            raise BuildError(f"provider certification lacks a pinned version: {provider}/{certification}")
        package_status = capabilities.get("package")
        package = contract.get("package")
        if package_status not in STATUSES or not isinstance(package, dict):
            raise BuildError(f"invalid package capability: {provider}")
        if package.get("status") != package_status:
            raise BuildError(f"package capability/build mismatch: {provider}")
        manifest_path = package.get("manifest_path")
        marketplace_path = package.get("marketplace_path")
        manifest_format = package.get("manifest_format", "distribution")
        context_file_name = package.get("context_file_name")
        components = package.get("components")
        if not isinstance(components, dict) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in components.items()
        ):
            raise BuildError(f"invalid package components: {provider}")
        unknown_components = set(components) - PACKAGE_COMPONENTS
        if unknown_components:
            raise BuildError(
                f"unknown package components for {provider}: {sorted(unknown_components)}"
            )
        if package_status == "supported":
            if not isinstance(manifest_path, str):
                raise BuildError(f"supported package has no manifest: {provider}")
            if manifest_format not in PACKAGE_MANIFEST_FORMATS:
                raise BuildError(f"unknown package manifest format: {provider}/{manifest_format}")
            if manifest_format == "gemini-extension":
                if not isinstance(context_file_name, str) or not context_file_name:
                    raise BuildError(f"Gemini extension has no context file: {provider}")
                _safe_relative(context_file_name, "provider package context file")
            elif context_file_name is not None:
                raise BuildError(f"unexpected package context file: {provider}")
            _safe_relative(manifest_path, "provider package manifest")
            if marketplace_path is not None:
                if not isinstance(marketplace_path, str):
                    raise BuildError(f"invalid package marketplace: {provider}")
                _safe_relative(marketplace_path, "provider package marketplace")
            for component_name, component_path in components.items():
                if not component_name or not component_path.startswith("./"):
                    raise BuildError(f"invalid package component: {provider}/{component_name}")
                _safe_relative(component_path[2:], "provider package component")
        elif (
            manifest_path is not None
            or marketplace_path is not None
            or components
            or "manifest_format" in package
            or context_file_name is not None
        ):
            raise BuildError(f"non-supported package has build behavior: {provider}")
        declared = capabilities.get("capabilities")
        implementations = contract.get("artifacts")
        if not isinstance(declared, dict) or set(declared) != set(ARTIFACT_TYPES):
            raise BuildError(f"incomplete capabilities: {provider}")
        if not isinstance(implementations, dict) or set(implementations) != set(ARTIFACT_TYPES):
            raise BuildError(f"incomplete build contract: {provider}")
        for artifact_type in ARTIFACT_TYPES:
            status = declared[artifact_type]
            implementation = implementations[artifact_type]
            if status not in STATUSES or not isinstance(implementation, dict):
                raise BuildError(f"invalid capability: {provider}/{artifact_type}")
            if implementation.get("status") != status:
                raise BuildError(f"capability/build mismatch: {provider}/{artifact_type}")
            if status == "supported":
                transform = implementation.get("transform")
                if (
                    transform not in TRANSFORM_TYPES
                    or artifact_type not in TRANSFORM_TYPES[transform]
                    or not isinstance(implementation.get("output_template"), str)
                ):
                    raise BuildError(f"supported capability is not implemented: {provider}/{artifact_type}")
            elif implementation.get("transform") != "none" or implementation.get("output_template") is not None:
                raise BuildError(f"non-supported capability has build behavior: {provider}/{artifact_type}")
        output_root = contract.get("output_root")
        if not isinstance(output_root, str):
            raise BuildError(f"provider output_root missing: {provider}")
        _safe_relative(output_root, "provider output root")
        providers.append(
            {
                "id": provider,
                "capabilities": capabilities,
                "contract": contract,
                "contract_hash": hashlib.sha256(
                    (directory / "build-contract.json").read_bytes()
                ).hexdigest(),
            }
        )
    if not providers:
        raise BuildError("no provider contracts found")
    return providers


def _alias(artifact: dict[str, Any], provider: str) -> str:
    alias = artifact["aliases"].get(provider, artifact["aliases"].get("default", artifact["id"]))
    if not ALIAS_RE.fullmatch(alias):
        raise BuildError(f"invalid alias for {provider}/{artifact['id']}: {alias}")
    return alias


def _tree_entries(root: Path, *, include_report: bool = True) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    if not root.exists():
        return entries
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        relative = path.relative_to(root).as_posix()
        if not include_report and relative == "build-report.json":
            continue
        mode = path.stat().st_mode & 0o777
        content_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        entries.append((relative, f"{mode:04o}:{content_hash}"))
    return entries


def _tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for relative, file_hash in _tree_entries(root, include_report=False):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_hash.encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    path.chmod(0o644)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _markdown_frontmatter(content: str) -> tuple[dict[str, str], str]:
    if not content.startswith("---\n"):
        return {}, content
    closing = content.find("\n---\n", 4)
    if closing < 0:
        raise BuildError("unterminated Markdown frontmatter")
    fields: dict[str, str] = {}
    for line in content[4:closing].splitlines():
        if not line or line.startswith((" ", "\t")) or ":" not in line:
            continue
        key, value = line.split(":", 1)
        normalized = value.strip()
        if (
            len(normalized) >= 2
            and normalized[0] in {'"', "'"}
            and normalized[-1] == normalized[0]
        ):
            normalized = normalized[1:-1]
        fields[key.strip()] = normalized
    return fields, content[closing + 5 :]


def _render_artifact(source: Path, transform: str) -> tuple[bytes, int]:
    if transform == "copy":
        return source.read_bytes(), source.stat().st_mode & 0o777
    if transform == "gemini-command":
        try:
            content = source.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:
            raise BuildError(f"Gemini command source is not UTF-8: {source}") from error
        frontmatter, body = _markdown_frontmatter(content)
        description = frontmatter.get("description", source.stem)
        prompt = body.strip() + "\n"
        prompt = prompt.replace("$ARGUMENTS", "{{args}}")
        rendered = (
            f"description = {json.dumps(description, ensure_ascii=False)}\n"
            f"prompt = {json.dumps(prompt, ensure_ascii=False)}\n"
        )
        return rendered.encode("utf-8"), 0o644
    raise BuildError(f"unknown artifact transform: {transform}")


def _build_provider_package(
    provider: dict[str, Any],
    distribution: dict[str, Any],
    output: Path,
    outputs: set[str],
) -> dict[str, Any]:
    provider_id = provider["id"]
    contract = provider["contract"]
    package = contract["package"]
    report_item: dict[str, Any] = {
        "provider": provider_id,
        "status": package["status"],
    }
    if package["status"] != "supported":
        return report_item

    manifest_relative = PurePosixPath(contract["output_root"]) / _safe_relative(
        package["manifest_path"], "provider package manifest"
    )
    manifest_text = manifest_relative.as_posix()
    if manifest_text in outputs:
        raise BuildError(f"output collision: {manifest_text}")
    outputs.add(manifest_text)
    manifest_format = package.get("manifest_format", "distribution")
    if manifest_format == "gemini-extension":
        manifest = {
            "name": distribution["name"],
            "version": distribution["version"],
            "description": distribution["description"],
            "contextFileName": package["context_file_name"],
        }
    else:
        manifest = {
            key: distribution[key]
            for key in (
                "name",
                "version",
                "description",
                "author",
                "homepage",
                "repository",
                "license",
                "keywords",
            )
        }
        manifest.update(package["components"])
    report_item.update(
        {
            "manifest": manifest_text,
            "manifest_sha256": _write_json(output / manifest_relative, manifest),
            "manifest_format": manifest_format,
        }
    )

    marketplace_path = package["marketplace_path"]
    if marketplace_path is not None:
        marketplace_relative = PurePosixPath(contract["output_root"]) / _safe_relative(
            marketplace_path, "provider package marketplace"
        )
        marketplace_text = marketplace_relative.as_posix()
        if marketplace_text in outputs:
            raise BuildError(f"output collision: {marketplace_text}")
        outputs.add(marketplace_text)
        marketplace_metadata = distribution["marketplace"]
        marketplace = {
            "name": marketplace_metadata["name"],
            "interface": {"displayName": marketplace_metadata["display_name"]},
            "plugins": [
                {
                    "name": distribution["name"],
                    "source": {"source": "local", "path": "./"},
                    "policy": {
                        "installation": marketplace_metadata["installation_policy"],
                        "authentication": marketplace_metadata["authentication_policy"],
                    },
                    "category": marketplace_metadata["category"],
                }
            ],
        }
        report_item.update(
            {
                "marketplace": marketplace_text,
                "marketplace_sha256": _write_json(output / marketplace_relative, marketplace),
            }
        )
    return report_item


def _build_into(root: Path, output: Path) -> dict[str, Any]:
    catalog_path = root / "core" / "catalog.yaml"
    catalog = _load_object(catalog_path, "catalog")
    distribution = _validate_distribution(catalog)
    artifacts = _validate_catalog(root, catalog)
    providers = _load_providers(root)
    provider_ids = {provider["id"] for provider in providers}
    for artifact in artifacts:
        unknown = set(artifact["providers"]) - provider_ids
        if unknown:
            raise BuildError(f"unknown providers for {artifact['id']}: {sorted(unknown)}")
    output.mkdir(parents=True, exist_ok=False)
    report_artifacts: list[dict[str, Any]] = []
    report_capabilities: list[dict[str, Any]] = []
    report_packages: list[dict[str, Any]] = []
    outputs: set[str] = set()
    aliases: set[tuple[str, str, str]] = set()

    for provider in providers:
        provider_id = provider["id"]
        contract = provider["contract"]
        report_packages.append(
            _build_provider_package(provider, distribution, output, outputs)
        )
        for artifact_type in ARTIFACT_TYPES:
            report_capabilities.append(
                {
                    "provider": provider_id,
                    "type": artifact_type,
                    "status": contract["artifacts"][artifact_type]["status"],
                }
            )
        for artifact in artifacts:
            if provider_id not in artifact["providers"]:
                continue
            artifact_type = artifact["type"]
            build_rule = contract["artifacts"][artifact_type]
            status = build_rule["status"]
            report_item: dict[str, Any] = {
                "provider": provider_id,
                "artifact_id": artifact["id"],
                "type": artifact_type,
                "status": status,
                "migration_state": artifact["migration_state"],
            }
            if status == "supported":
                alias = _alias(artifact, provider_id)
                alias_key = (provider_id, artifact_type, alias)
                if alias_key in aliases:
                    raise BuildError(f"alias collision: {provider_id}/{artifact_type}/{alias}")
                aliases.add(alias_key)
                output_template = build_rule["output_template"]
                try:
                    rendered_output = output_template.format(id=artifact["id"], alias=alias)
                except (KeyError, ValueError) as error:
                    raise BuildError(
                        f"invalid output template for {provider_id}/{artifact_type}: "
                        f"{output_template!r} ({error})"
                    ) from error
                relative = PurePosixPath(contract["output_root"]) / _safe_relative(
                    rendered_output,
                    "artifact output",
                )
                relative_text = relative.as_posix()
                if relative_text in outputs:
                    raise BuildError(f"output collision: {relative_text}")
                outputs.add(relative_text)
                target = output / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                source = root / artifact["source"]
                transform = build_rule["transform"]
                content, mode = _render_artifact(source, transform)
                target.write_bytes(content)
                target.chmod(mode)
                report_item.update(
                    {
                        "alias": alias,
                        "output": relative_text,
                        "mode": f"{target.stat().st_mode & 0o777:04o}",
                        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                        "transform": transform,
                    }
                )
            report_artifacts.append(report_item)

    for provider in providers:
        contract = provider["contract"]
        package = contract["package"]
        if package["status"] != "supported":
            continue
        output_root = PurePosixPath(contract["output_root"])
        if package.get("manifest_format", "distribution") == "gemini-extension":
            context_output = (
                output_root
                / _safe_relative(package["context_file_name"], "provider package context file")
            ).as_posix()
            if context_output not in outputs:
                raise BuildError(f"Gemini extension context is not generated: {context_output}")
        for component_name, component_path in package["components"].items():
            component_prefix = (
                output_root
                / _safe_relative(component_path[2:], "provider package component")
            ).as_posix().rstrip("/") + "/"
            if not any(output.startswith(component_prefix) for output in outputs):
                raise BuildError(
                    f"package component has no generated artifacts: "
                    f"{provider['id']}/{component_name}"
                )

    report = {
        "schema_version": 1,
        "distribution": {
            "name": distribution["name"],
            "version": distribution["version"],
        },
        "catalog_hash": hashlib.sha256(catalog_path.read_bytes()).hexdigest(),
        "providers": [provider["id"] for provider in providers],
        "provider_contract_hashes": {
            provider["id"]: provider["contract_hash"] for provider in providers
        },
        "packages": report_packages,
        "capabilities": report_capabilities,
        "artifacts": report_artifacts,
        "tree_hash": _tree_hash(output),
    }
    (output / "build-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def build_repository(root: Path, output: Path) -> dict[str, Any]:
    root = root.resolve()
    output = output.resolve()
    if output in {Path("/").resolve(), root}:
        raise BuildError(f"unsafe build output: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_parent = Path(tempfile.mkdtemp(prefix=f".{output.name}.build-", dir=output.parent))
    candidate = temporary_parent / "candidate"
    backup: Path | None = None
    try:
        report = _build_into(root, candidate)
        if output.exists():
            backup = output.parent / f".{output.name}.backup-{uuid.uuid4().hex}"
            os.replace(output, backup)
        os.replace(candidate, output)
        if backup is not None:
            shutil.rmtree(backup)
        return report
    except Exception:
        if backup is not None and backup.exists() and not output.exists():
            os.replace(backup, output)
        raise
    finally:
        shutil.rmtree(temporary_parent, ignore_errors=True)


def compare_trees(expected: Path, actual: Path) -> list[str]:
    expected_entries = dict(_tree_entries(expected))
    actual_entries = dict(_tree_entries(actual))
    differences: list[str] = []
    for relative in sorted(set(expected_entries) | set(actual_entries)):
        if relative not in expected_entries:
            differences.append(f"orphan output: {relative}")
        elif relative not in actual_entries:
            differences.append(f"missing output: {relative}")
        elif expected_entries[relative] != actual_entries[relative]:
            differences.append(f"modified output: {relative}")
    return differences


def check_repository(root: Path, output: Path) -> list[str]:
    with tempfile.TemporaryDirectory(prefix="skillz-build-check-") as temporary:
        expected = Path(temporary) / "dist"
        _build_into(root.resolve(), expected)
        return compare_trees(expected, output.resolve())


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "check"))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=Path("dist"))
    args = parser.parse_args(argv)
    output = args.output if args.output.is_absolute() else args.root / args.output
    try:
        if args.action == "build":
            report = build_repository(args.root, output)
            print(json.dumps({"status": "built", "tree_hash": report["tree_hash"]}, sort_keys=True))
            return 0
        differences = check_repository(args.root, output)
        if differences:
            print("\n".join(differences), file=sys.stderr)
            return 1
        print(json.dumps({"status": "clean", "output": str(output)}, sort_keys=True))
        return 0
    except (BuildError, OSError) as error:
        print(f"provider build failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
