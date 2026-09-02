#!/usr/bin/env python3
"""Migrate legacy Claude artifacts into the provider-neutral core catalog."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any


ALL_PROVIDERS = ["claude", "codex", "opencode", "agents-generic", "kimi", "grok", "gemini"]
PATH_TOKEN = re.compile(r"(?<!~/)\.claude/skills/([a-z0-9-]+)(?:/SKILL\.md|/)?")
COMMAND_TOKEN = re.compile(r"(?<!~/)\.claude/commands/([a-z0-9-]+)\.md")
KNOWLEDGE_TOKEN = re.compile(
    r"(?:(?<!~/)\.claude/knowledge/|(?:\.\./)+knowledge/)([A-Za-z0-9_./-]+)"
)
PORTABLE_FRONTMATTER = {"name", "description", "license"}
GENERATED_RESOURCE_DIRECTORIES = {"__pycache__", "node_modules"}
GENERATED_RESOURCE_SUFFIXES = {".pyc", ".pyo"}

RISK_FOUR = {
    "dev-workflow", "quality-gate", "ship-workflow", "security-auditor",
    "supabase-security", "thermo-nuclear-code-quality-review", "ship",
}
RISK_THREE = {
    "architect", "code-implementer", "code-reviewer", "database-designer",
    "design-audit", "figma-generate-library", "orchestrate", "project-probe",
    "seo-geo-audit", "test-runner", "dev", "pr-review", "seo-geo-squad",
}
CURATED_CANONICAL = {
    "dev-workflow", "discovery-workflow", "project-probe", "quality-gate",
    "ship-workflow", "status-workflow",
}
SHARED_SKILL_RESOURCES = {
    "project-probe": (
        "scripts/project_probe.py",
        "scripts/run-python310.sh",
    ),
    "quality-gate": (
        "scripts/gate_verify.py",
        "scripts/run-python310.sh",
    ),
}


class MigrationError(RuntimeError):
    """Raised when migration would lose a required file or reference."""


def _entry_name(path: Path, identifier: str) -> str:
    text = path.read_text(encoding="utf-8")
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            for line in text[4:end].splitlines():
                if line.startswith("name:"):
                    value = line.split(":", 1)[1].strip().strip("'\"")
                    if value:
                        return value
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return identifier.replace("-", " ").title()


def _knowledge_paths(text: str) -> list[str]:
    matches = {match.rstrip("`'\"),.:;") for match in KNOWLEDGE_TOKEN.findall(text)}
    return sorted(match for match in matches if PurePosixPath(match).suffix)


def _safe_knowledge_path(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise MigrationError(f"unsafe knowledge resource path: {value}")
    return path


def _regular_files(directory: Path, entrypoint: Path | None = None) -> list[Path]:
    files: list[Path] = []
    for item in sorted(directory.rglob("*")):
        relative = item.relative_to(directory)
        if (
            GENERATED_RESOURCE_DIRECTORIES.intersection(relative.parts)
            or item.suffix in GENERATED_RESOURCE_SUFFIXES
        ):
            continue
        if item.is_symlink():
            raise MigrationError(f"symlink is not allowed in canonical resources: {item}")
        if item.is_file() and item != entrypoint:
            files.append(item)
    return files


def _partition_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        return text, ""
    closing = text.find("\n---\n", 4)
    if closing < 0:
        raise MigrationError("unterminated artifact frontmatter")
    lines = text[4:closing].splitlines()
    groups: list[tuple[str, list[str]]] = []
    for line in lines:
        if line and not line[0].isspace() and ":" in line:
            groups.append((line.split(":", 1)[0], [line]))
        elif not groups:
            raise MigrationError("frontmatter content appears before its first key")
        else:
            groups[-1][1].append(line)
    portable = [line for key, group in groups if key in PORTABLE_FRONTMATTER for line in group]
    provider = [line for key, group in groups if key not in PORTABLE_FRONTMATTER for line in group]
    body = text[closing + 5 :]
    canonical = "---\n" + "\n".join(portable) + "\n---\n" + body
    fragment = "\n".join(provider) + ("\n" if provider else "")
    return canonical, fragment


def _normalize_paths(text: str, artifact_type: str, identifier: str) -> str:
    text = COMMAND_TOKEN.sub(lambda match: f"command:{match.group(1)}", text)

    def skill_reference(match: re.Match[str]) -> str:
        matched = match.group(0)
        suffix = "" if matched.endswith("SKILL.md") else ("/" if matched.endswith("/") else "")
        return f"skill:{match.group(1)}{suffix}"

    text = PATH_TOKEN.sub(skill_reference, text)
    text = re.sub(r"(?<!~/)\.claude/skills/", "core/skills/", text)
    text = re.sub(r"(?<!~/)\.claude/commands/", "core/commands/", text)
    if artifact_type == "skill":
        text = KNOWLEDGE_TOKEN.sub(lambda match: f"references/knowledge/{match.group(1)}", text)
    else:
        text = KNOWLEDGE_TOKEN.sub(
        lambda match: f"resources/{identifier}/knowledge/{match.group(1)}", text
        )
    return re.sub(r"(?<!~/)\.claude/knowledge/", "core/knowledge/", text)


def _normalize_entry(text: str, artifact_type: str, identifier: str) -> str:
    canonical, _ = _partition_frontmatter(_normalize_paths(text, artifact_type, identifier))
    return canonical


def _provider_frontmatter(text: str, artifact_type: str, identifier: str) -> str:
    _, fragment = _partition_frontmatter(_normalize_paths(text, artifact_type, identifier))
    return fragment


def _risk(identifier: str) -> int:
    if identifier in RISK_FOUR:
        return 4
    if identifier in RISK_THREE:
        return 3
    if any(token in identifier for token in ("audit", "review", "doctor", "gate")):
        return 3
    if any(token in identifier for token in ("status", "docs", "metrics", "changelog")):
        return 1
    return 2


def _dependencies(text: str, identifier: str, known: set[str]) -> list[str]:
    referenced = set(re.findall(r"\bskill:([a-z0-9-]+)", text))
    return sorted((referenced & known) - {identifier})


def _resource_items(root: Path, artifact_type: str, identifier: str, source: Path) -> list[dict[str, str]]:
    resources: list[dict[str, str]] = []
    if artifact_type == "skill":
        directory = source.parent
        for path in _regular_files(directory, source):
            resources.append({
                "source": path.relative_to(root).as_posix(),
                "output": path.relative_to(directory).as_posix(),
            })
        for shared in SHARED_SKILL_RESOURCES.get(identifier, ()):
            shared_path = root / shared
            if not shared_path.is_file() or shared_path.is_symlink():
                raise MigrationError(f"missing shared skill resource: {shared}")
            resources.append({"source": shared, "output": shared})

    legacy_entry = (
        root / ".claude" / "skills" / identifier / "SKILL.md"
        if artifact_type == "skill"
        else root / ".claude" / "commands" / f"{identifier}.md"
    )
    reference_text = (
        legacy_entry.read_text(encoding="utf-8")
        if legacy_entry.is_file() and identifier not in CURATED_CANONICAL
        else source.read_text(encoding="utf-8")
    )
    for knowledge in _knowledge_paths(reference_text):
        safe_knowledge = _safe_knowledge_path(knowledge)
        knowledge_source = root / "core" / "knowledge" / safe_knowledge
        if not knowledge_source.is_file() or knowledge_source.is_symlink():
            raise MigrationError(f"missing knowledge resource: {knowledge_source.relative_to(root)}")
        output = (
            f"references/knowledge/{knowledge}"
            if artifact_type == "skill"
            else f"resources/{identifier}/knowledge/{knowledge}"
        )
        item = {"source": knowledge_source.relative_to(root).as_posix(), "output": output}
        if output not in {resource["output"] for resource in resources}:
            resources.append(item)
    return sorted(resources, key=lambda item: item["output"])


def _copy_artifacts(root: Path, *, extract_provider_metadata: bool = False) -> None:
    pairs: list[tuple[Path, Path, str, str]] = []
    for legacy in sorted((root / ".claude" / "skills").glob("*/SKILL.md")):
        identifier = legacy.parent.name
        pairs.append((legacy, root / "core" / "skills" / identifier / "SKILL.md", "skill", identifier))
    for legacy in sorted((root / ".claude" / "commands").glob("*.md")):
        identifier = legacy.stem
        pairs.append((legacy, root / "core" / "commands" / legacy.name, "command", identifier))

    for legacy, canonical, artifact_type, identifier in pairs:
        if legacy.is_symlink():
            raise MigrationError(f"symlink entrypoint is not allowed: {legacy.relative_to(root)}")
        expected = _normalize_entry(legacy.read_text(encoding="utf-8"), artifact_type, identifier)
        if canonical.is_symlink():
            raise MigrationError(f"symlink canonical entrypoint is not allowed: {canonical.relative_to(root)}")
        if canonical.exists() and identifier not in CURATED_CANONICAL:
            current_canonical = canonical.read_text(encoding="utf-8")
            if current_canonical != expected:
                pre_extraction = _normalize_paths(
                    legacy.read_text(encoding="utf-8"), artifact_type, identifier
                )
                normalized_current = _normalize_paths(current_canonical, artifact_type, identifier)
                safe_extraction_state = current_canonical == pre_extraction or normalized_current == expected
                if extract_provider_metadata and safe_extraction_state:
                    canonical.write_text(expected, encoding="utf-8")
                else:
                    raise MigrationError(f"canonical entry drift blocks migration: {canonical.relative_to(root)}")
        elif not canonical.exists():
            canonical.parent.mkdir(parents=True, exist_ok=True)
            canonical.write_text(expected, encoding="utf-8")
            canonical.chmod(legacy.stat().st_mode & 0o777)
        if artifact_type != "skill":
            continue
        for resource in _regular_files(legacy.parent, legacy):
            target = canonical.parent / resource.relative_to(legacy.parent)
            if target.is_symlink():
                raise MigrationError(f"symlink canonical resource is not allowed: {target.relative_to(root)}")
            if target.exists() and target.read_bytes() != resource.read_bytes():
                raise MigrationError(f"canonical resource drift blocks migration: {target.relative_to(root)}")
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                shutil.copy2(resource, target)

    referenced_knowledge: set[str] = set()
    for entry in [
        *(root / ".claude" / "skills").glob("*/SKILL.md"),
        *(root / ".claude" / "commands").glob("*.md"),
    ]:
        referenced_knowledge.update(_knowledge_paths(entry.read_text(encoding="utf-8")))
    for relative in sorted(referenced_knowledge):
        safe_relative = _safe_knowledge_path(relative)
        source = root / ".claude" / "knowledge" / safe_relative
        if not source.is_file() or source.is_symlink():
            raise MigrationError(f"missing knowledge resource: {source.relative_to(root)}")
        target = root / "core" / "knowledge" / safe_relative
        if target.is_symlink():
            raise MigrationError(f"symlink canonical knowledge is not allowed: {target.relative_to(root)}")
        if target.exists() and target.read_bytes() != source.read_bytes():
            raise MigrationError(f"canonical knowledge drift blocks migration: {target.relative_to(root)}")
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            shutil.copy2(source, target)


def _artifact(
    root: Path,
    artifact_type: str,
    artifact_id: str,
    identifier: str,
    source: Path,
    previous: dict[str, Any] | None,
    known_skills: set[str],
) -> dict[str, Any]:
    text = source.read_text(encoding="utf-8")
    result: dict[str, Any] = {
        "id": artifact_id,
        "public_name": previous.get("public_name") if previous else _entry_name(source, identifier),
        "type": artifact_type,
        "source": source.relative_to(root).as_posix(),
        "dependencies": _dependencies(text, identifier, known_skills),
        "inputs": previous.get("inputs", ["task"]) if previous else ["task"],
        "outputs": previous.get("outputs", ["result"]) if previous else ["result"],
        "aliases": previous.get("aliases", {"default": identifier}) if previous else {"default": identifier},
        "providers": previous.get("providers", ALL_PROVIDERS) if previous else ALL_PROVIDERS,
        "risk": previous.get("risk", _risk(identifier)) if previous else _risk(identifier),
        "migration_state": "canonical",
    }
    result["dependencies"] = sorted(set(result["dependencies"]) | set(previous.get("dependencies", []) if previous else []))
    resources = _resource_items(root, artifact_type, identifier, source)
    if resources:
        result["resources"] = resources
    legacy_entry = (
        root / ".claude" / "skills" / identifier / "SKILL.md"
        if artifact_type == "skill"
        else root / ".claude" / "commands" / f"{identifier}.md"
    )
    if legacy_entry.is_file():
        fragment = _provider_frontmatter(
            legacy_entry.read_text(encoding="utf-8"), artifact_type, identifier
        )
        if fragment:
            result["provider_metadata"] = {"claude": {"frontmatter": fragment}}
    return result


def _build_catalog(root: Path, current: dict[str, Any]) -> dict[str, Any]:
    previous = {
        (item["type"], item.get("aliases", {}).get("default", item["id"])): item
        for item in current["artifacts"]
    }
    skills = sorted((root / "core" / "skills").glob("*/SKILL.md"))
    commands = sorted((root / "core" / "commands").glob("*.md"))
    known_skills = {path.parent.name for path in skills}
    artifacts = [
        _artifact(
            root,
            "skill",
            path.parent.name,
            path.parent.name,
            path,
            previous.get(("skill", path.parent.name)),
            known_skills,
        )
        for path in skills
    ]
    artifacts.extend(
        _artifact(
            root,
            "command",
            f"{path.stem}-command" if path.stem in known_skills else path.stem,
            path.stem,
            path,
            previous.get(("command", path.stem)),
            known_skills,
        )
        for path in commands
    )
    artifacts.extend(item for item in current["artifacts"] if item["type"] not in {"skill", "command"})
    return {"schema_version": current["schema_version"], "distribution": current["distribution"], "artifacts": artifacts}


def _check(root: Path, catalog: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    artifacts = {item["id"]: item for item in catalog["artifacts"]}
    skill_artifacts = {
        item.get("aliases", {}).get("default", item["id"]): item
        for item in catalog["artifacts"]
        if item["type"] == "skill"
    }
    command_artifacts = {
        item.get("aliases", {}).get("default", item["id"]): item
        for item in catalog["artifacts"]
        if item["type"] == "command"
    }
    legacy_skills = {path.parent.name for path in (root / ".claude" / "skills").glob("*/SKILL.md")}
    legacy_commands = {path.stem for path in (root / ".claude" / "commands").glob("*.md")}
    canonical_skills = {path.parent.name for path in (root / "core" / "skills").glob("*/SKILL.md")}
    canonical_commands = {path.stem for path in (root / "core" / "commands").glob("*.md")}
    catalog_skills = set(skill_artifacts)
    catalog_commands = set(command_artifacts)
    if canonical_skills != catalog_skills:
        errors.append(f"skill inventory mismatch: missing={sorted(canonical_skills - catalog_skills)} extra={sorted(catalog_skills - canonical_skills)}")
    if canonical_commands != catalog_commands:
        errors.append(f"command inventory mismatch: missing={sorted(canonical_commands - catalog_commands)} extra={sorted(catalog_commands - canonical_commands)}")
    if legacy_skills - canonical_skills:
        errors.append(f"legacy skill coverage mismatch: missing={sorted(legacy_skills - canonical_skills)}")
    if legacy_commands - canonical_commands:
        errors.append(f"legacy command coverage mismatch: missing={sorted(legacy_commands - canonical_commands)}")

    for artifact_type, identifiers, by_alias in (
        ("skill", legacy_skills, skill_artifacts),
        ("command", legacy_commands, command_artifacts),
    ):
        for identifier in sorted(identifiers):
            legacy = (
                root / ".claude" / "skills" / identifier / "SKILL.md"
                if artifact_type == "skill"
                else root / ".claude" / "commands" / f"{identifier}.md"
            )
            artifact = by_alias.get(identifier)
            if not artifact:
                continue
            canonical = root / artifact["source"]
            expected = _normalize_entry(legacy.read_text(encoding="utf-8"), artifact_type, identifier)
            if identifier not in CURATED_CANONICAL and canonical.read_text(encoding="utf-8") != expected:
                errors.append(f"canonical {artifact_type} entry drift: {identifier}")
            _, expected_fragment = _partition_frontmatter(
                _normalize_paths(legacy.read_text(encoding="utf-8"), artifact_type, identifier)
            )
            actual_fragment = artifact.get("provider_metadata", {}).get("claude", {}).get("frontmatter", "")
            if actual_fragment != expected_fragment:
                errors.append(f"provider frontmatter drift: {identifier}")
            declared = {item["output"]: item["source"] for item in artifact.get("resources", [])}
            actual_items = _resource_items(root, artifact_type, identifier, canonical)
            if declared != {item["output"]: item["source"] for item in actual_items}:
                errors.append(f"resource manifest drift: {identifier}")
            if artifact_type == "skill" and identifier not in CURATED_CANONICAL:
                for resource in actual_items:
                    if not resource["source"].startswith("core/skills/"):
                        continue
                    legacy_resource = legacy.parent / resource["output"]
                    canonical_resource = root / resource["source"]
                    if not legacy_resource.is_file() or legacy_resource.read_bytes() != canonical_resource.read_bytes():
                        errors.append(f"canonical resource drift: {identifier}/{resource['output']}")

    for artifact_type, identifiers, by_alias in (
        ("skill", canonical_skills - legacy_skills, skill_artifacts),
        ("command", canonical_commands - legacy_commands, command_artifacts),
    ):
        for identifier in sorted(identifiers):
            artifact = by_alias.get(identifier)
            if not artifact:
                continue
            canonical = root / artifact["source"]
            declared = {item["output"]: item["source"] for item in artifact.get("resources", [])}
            actual_items = _resource_items(root, artifact_type, identifier, canonical)
            if declared != {item["output"]: item["source"] for item in actual_items}:
                errors.append(f"resource manifest drift: {identifier}")

    for artifact in artifacts.values():
        if artifact["type"] in {"skill", "command"} and (
            artifact["migration_state"] != "canonical" or not artifact["source"].startswith("core/")
        ):
            errors.append(f"non-canonical catalog source: {artifact['id']}")
    for legacy in sorted((root / ".claude" / "knowledge").rglob("*")):
        if not legacy.is_file():
            continue
        canonical = root / "core" / "knowledge" / legacy.relative_to(root / ".claude" / "knowledge")
        if canonical.exists() and canonical.read_bytes() != legacy.read_bytes():
            errors.append(f"canonical knowledge drift: {canonical.relative_to(root)}")
    return errors


def _report(catalog: dict[str, Any]) -> dict[str, Any]:
    aliases: dict[str, list[str]] = {}
    for artifact in catalog["artifacts"]:
        alias = artifact.get("aliases", {}).get("default", artifact["id"])
        aliases.setdefault(alias, []).append(f"{artifact['type']}:{artifact['id']}")
    return {
        "schema_version": 1,
        "status": "PASS",
        "catalog_artifacts": len(catalog["artifacts"]),
        "catalog_resources": sum(len(item.get("resources", [])) for item in catalog["artifacts"]),
        "provider_metadata_artifacts": sum(bool(item.get("provider_metadata")) for item in catalog["artifacts"]),
        "counts": {
            kind: sum(1 for item in catalog["artifacts"] if item["type"] == kind)
            for kind in ("skill", "command", "instruction")
        },
        "migration_states": {
            state: sum(1 for item in catalog["artifacts"] if item["migration_state"] == state)
            for state in ("canonical", "legacy", "pending", "retired")
        },
        "shared_aliases": {
            alias: sorted(owners) for alias, owners in sorted(aliases.items()) if len(owners) > 1
        },
        "legacy_mirrors_preserved": True,
        "artifacts": [
            {
                "id": item["id"],
                "type": item["type"],
                "alias": item.get("aliases", {}).get("default", item["id"]),
                "source": item["source"],
                "migration_state": item["migration_state"],
                "resource_count": len(item.get("resources", [])),
            }
            for item in catalog["artifacts"]
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--extract-provider-metadata", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    catalog_path = root / "core" / "catalog.yaml"
    current = json.loads(catalog_path.read_text(encoding="utf-8"))
    if args.extract_provider_metadata and not args.apply:
        parser.error("--extract-provider-metadata requires --apply")
    if args.apply:
        _copy_artifacts(root, extract_provider_metadata=args.extract_provider_metadata)
        current = _build_catalog(root, current)
        catalog_path.write_text(json.dumps(current, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    errors = _check(root, current)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    report = _report(current)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        report_path = args.report if args.report.is_absolute() else root / args.report
        if args.apply:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(rendered, encoding="utf-8")
        elif not report_path.is_file() or report_path.read_text(encoding="utf-8") != rendered:
            print(f"ERROR: stale catalog migration report: {report_path}", file=sys.stderr)
            return 1
    print(json.dumps({"status": "PASS", "counts": report["counts"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
