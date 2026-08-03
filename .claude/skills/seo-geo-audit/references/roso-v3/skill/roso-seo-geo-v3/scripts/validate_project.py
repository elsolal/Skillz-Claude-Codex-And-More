#!/usr/bin/env python3
"""Validate a RosoAI V3 project against schemas and cross-file invariants."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from _common import find_kit_root, load_simple_yaml, parse_datetime, read_json, read_jsonl, validate_schema


SCHEMA_FILES = {
    "audit_manifest.json": "audit_manifest.schema.json",
    "facts.json": "facts.schema.json",
    "findings.json": "findings.schema.json",
    "actions.json": "actions.schema.json",
}


def issue(code: str, path: str, message: str, severity: str = "error") -> dict[str, str]:
    return {"severity": severity, "code": code, "path": path, "message": message}


def _load_required_json(project: Path, filename: str, issues: list[dict[str, str]]) -> Any | None:
    path = project / filename
    if not path.is_file():
        issues.append(issue("missing_file", filename, "Fichier requis absent."))
        return None
    try:
        return read_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        issues.append(issue("invalid_json", filename, str(exc)))
        return None


def _validate_dates(data: dict[str, Any], fields: tuple[str, str], path: str, issues: list[dict[str, str]]) -> None:
    left, right = fields
    if data.get(left) and data.get(right):
        try:
            if parse_datetime(data[right]) < parse_datetime(data[left]):
                issues.append(issue("date_order", path, f"{right} est antérieur à {left}."))
        except (TypeError, ValueError):
            pass


def _object(value: Any) -> dict[str, Any]:
    """Return a mapping for cross-file checks after schema errors were recorded."""
    return value if isinstance(value, dict) else {}


def _records(value: Any, key: str) -> list[dict[str, Any]]:
    if not isinstance(value, dict) or not isinstance(value.get(key), list):
        return []
    return [record for record in value[key] if isinstance(record, dict)]


def validate_project(project: Path, kit_root: Path | None = None) -> list[dict[str, str]]:
    project = project.resolve()
    issues: list[dict[str, str]] = []
    try:
        kit_root = find_kit_root(kit_root)
    except FileNotFoundError as exc:
        return [issue("kit_root", str(project), str(exc))]
    schemas_dir = kit_root / "schemas"

    schemas: dict[str, dict[str, Any]] = {}
    for schema_path in sorted(schemas_dir.glob("*.schema.json")):
        try:
            schema = read_json(schema_path)
            schemas[schema_path.name] = schema
            try:
                import jsonschema  # type: ignore

                jsonschema.Draft202012Validator.check_schema(schema)
            except ImportError:
                pass
            except Exception as exc:
                issues.append(issue("invalid_schema", str(schema_path), str(exc)))
        except (OSError, json.JSONDecodeError) as exc:
            issues.append(issue("invalid_schema_json", str(schema_path), str(exc)))

    loaded: dict[str, Any] = {}
    for filename, schema_name in SCHEMA_FILES.items():
        data = _load_required_json(project, filename, issues)
        if data is None:
            continue
        loaded[filename] = data
        schema = schemas.get(schema_name)
        if not schema:
            issues.append(issue("missing_schema", schema_name, "Schéma requis absent."))
            continue
        for message in validate_schema(data, schema):
            issues.append(issue("schema", filename, message))

    client_path = project / "client.yaml"
    client: dict[str, Any] | None = None
    if not client_path.is_file():
        issues.append(issue("missing_file", "client.yaml", "Fichier requis absent."))
    else:
        try:
            client = load_simple_yaml(client_path)
            if client.get("schema_version") != "3.0":
                issues.append(issue("client_schema_version", "client.yaml", "schema_version doit valoir 3.0."))
            for key in ("client_id", "identity", "business", "markets", "brand_governance", "contacts"):
                if key not in client:
                    issues.append(issue("client_required", "client.yaml", f"Clé requise absente: {key}."))
        except (OSError, ValueError) as exc:
            issues.append(issue("invalid_yaml", "client.yaml", str(exc)))

    ledgers: dict[str, list[dict[str, Any]]] = {}
    for filename, schema_name in (("evidence.jsonl", "evidence.schema.json"), ("events.jsonl", "events.schema.json")):
        path = project / filename
        if not path.is_file():
            issues.append(issue("missing_file", filename, "Fichier requis absent."))
            continue
        try:
            records = read_jsonl(path)
            ledgers[filename] = records
            schema = schemas.get(schema_name)
            if not schema:
                issues.append(issue("missing_schema", schema_name, "Schéma requis absent."))
            else:
                for index, record in enumerate(records, 1):
                    for message in validate_schema(record, schema):
                        issues.append(issue("schema", f"{filename}:{index}", message))
        except (OSError, ValueError) as exc:
            issues.append(issue("invalid_jsonl", filename, str(exc)))

    geo_runs: list[dict[str, Any]] = []
    geo_dir = project / "geo_runs"
    if not geo_dir.is_dir():
        issues.append(issue("missing_directory", "geo_runs", "Dossier requis absent."))
    else:
        geo_schema = schemas.get("geo_run.schema.json")
        for path in sorted(geo_dir.glob("*.json")):
            try:
                run = read_json(path)
                if isinstance(run, dict):
                    geo_runs.append(run)
                if geo_schema:
                    for message in validate_schema(run, geo_schema):
                        issues.append(issue("schema", str(path.relative_to(project)), message))
            except (OSError, json.JSONDecodeError) as exc:
                issues.append(issue("invalid_json", str(path.relative_to(project)), str(exc)))

    manifest = _object(loaded.get("audit_manifest.json"))
    audit_id = manifest.get("audit_id")
    if client and manifest and client.get("client_id") != manifest.get("client_id"):
        issues.append(issue("client_id_mismatch", "client.yaml", "client_id ne correspond pas au manifeste."))
    _validate_dates(manifest, ("created_at", "updated_at"), "audit_manifest.json", issues)

    evidence = ledgers.get("evidence.jsonl", [])
    facts = _records(loaded.get("facts.json"), "facts")
    findings = _records(loaded.get("findings.json"), "findings")
    actions = _records(loaded.get("actions.json"), "actions")
    events = ledgers.get("events.jsonl", [])

    collections = {
        "evidence": (evidence, "evidence_id"), "facts": (facts, "fact_id"), "findings": (findings, "finding_id"),
        "actions": (actions, "action_id"), "geo_runs": (geo_runs, "run_id"), "events": (events, "event_id"),
    }
    ids: dict[str, set[str]] = {}
    for label, (records, key) in collections.items():
        seen: set[str] = set()
        for index, record in enumerate(records):
            record_id = record.get(key)
            if record_id in seen:
                issues.append(issue("duplicate_id", label, f"Identifiant dupliqué: {record_id}."))
            if record_id:
                seen.add(record_id)
            if audit_id and label in {"evidence", "geo_runs", "events"} and record.get("audit_id") != audit_id:
                issues.append(issue("audit_id_mismatch", f"{label}[{index}]", "audit_id ne correspond pas au manifeste."))
        ids[label] = seen

    for filename in ("facts.json", "findings.json", "actions.json"):
        document = _object(loaded.get(filename))
        if audit_id and document and document.get("audit_id") != audit_id:
            issues.append(issue("audit_id_mismatch", filename, "audit_id ne correspond pas au manifeste."))

    for index, event in enumerate(events):
        try:
            if manifest.get("created_at") and parse_datetime(event.get("at")) < parse_datetime(manifest["created_at"]):
                issues.append(issue(
                    "event_before_audit", f"events[{index}].at",
                    "Un événement ne peut pas précéder la création de l’audit.",
                ))
        except (TypeError, ValueError):
            pass

    for index, record in enumerate(evidence):
        _validate_dates(record, ("collected_at", "expires_at"), f"evidence[{index}]", issues)
        raw_path = record.get("raw_path")
        if raw_path:
            try:
                (project / raw_path).resolve().relative_to(project)
            except (ValueError, OSError):
                issues.append(issue("unsafe_path", f"evidence[{index}].raw_path", "Le chemin brut doit rester relatif au projet."))
        permission = record.get("authorization_permission")
        if permission and permission not in manifest.get("authorization", {}).get("permissions", []):
            issues.append(issue("unauthorized_source", f"evidence[{index}]", f"Permission non accordée dans le manifeste: {permission}."))
    for index, record in enumerate(facts):
        for ref in record.get("evidence_ids", []):
            if ref not in ids.get("evidence", set()):
                issues.append(issue("missing_reference", f"facts[{index}].evidence_ids", f"Preuve inconnue: {ref}."))
    for index, record in enumerate(findings):
        for ref in record.get("evidence_ids", []):
            if ref not in ids.get("evidence", set()):
                issues.append(issue("missing_reference", f"findings[{index}].evidence_ids", f"Preuve inconnue: {ref}."))
        for ref in record.get("fact_ids", []):
            if ref not in ids.get("facts", set()):
                issues.append(issue("missing_reference", f"findings[{index}].fact_ids", f"Fait inconnu: {ref}."))
    for index, record in enumerate(actions):
        action_id = record.get("action_id")
        for ref in record.get("finding_ids", []):
            if ref not in ids.get("findings", set()):
                issues.append(issue("missing_reference", f"actions[{index}].finding_ids", f"Constat inconnu: {ref}."))
        for ref in record.get("evidence_ids", []):
            if ref not in ids.get("evidence", set()):
                issues.append(issue("missing_reference", f"actions[{index}].evidence_ids", f"Preuve inconnue: {ref}."))
        for ref in record.get("dependencies", []):
            if ref == action_id:
                issues.append(issue("self_dependency", f"actions[{index}].dependencies", "Une action ne peut pas dépendre d'elle-même."))
            elif ref not in ids.get("actions", set()):
                issues.append(issue("missing_reference", f"actions[{index}].dependencies", f"Action dépendante inconnue: {ref}."))
    for index, run in enumerate(geo_runs):
        _validate_dates(run, ("started_at", "completed_at"), f"geo_runs[{index}]", issues)
        if isinstance(run.get("repeat_index"), int) and isinstance(run.get("total_repeats"), int) and run["repeat_index"] > run["total_repeats"]:
            issues.append(issue("repeat_index", f"geo_runs[{index}]", "repeat_index dépasse total_repeats."))

        prompt_ids: set[str] = set()
        for observation_index, observation in enumerate(run.get("observations", [])):
            if not isinstance(observation, dict):
                continue
            observation_path = f"geo_runs[{index}].observations[{observation_index}]"
            prompt_id = observation.get("prompt_id")
            if isinstance(prompt_id, str):
                if prompt_id in prompt_ids:
                    issues.append(issue(
                        "duplicate_geo_prompt", observation_path,
                        f"Le prompt {prompt_id} apparaît plusieurs fois dans le même run/répétition.",
                    ))
                prompt_ids.add(prompt_id)
            response_hash = observation.get("response_hash")
            evidence_id = observation.get("evidence_id")
            if not (isinstance(response_hash, str) and response_hash) and not (isinstance(evidence_id, str) and evidence_id):
                issues.append(issue(
                    "geo_provenance", observation_path,
                    "Une observation GEO doit référencer une empreinte de réponse ou une preuve.",
                ))
            if isinstance(evidence_id, str) and evidence_id not in ids.get("evidence", set()):
                issues.append(issue(
                    "missing_reference", f"{observation_path}.evidence_id",
                    f"Preuve inconnue: {evidence_id}.",
                ))

    repeat_slots: dict[tuple[Any, ...], str] = {}
    for index, run in enumerate(geo_runs):
        brand = run.get("brand", {}) if isinstance(run.get("brand"), dict) else {}
        session = run.get("session", {}) if isinstance(run.get("session"), dict) else {}
        run_context = (
            brand.get("name"), brand.get("domain"), tuple(sorted(brand.get("aliases", []))),
            run.get("engine"), run.get("model"), run.get("surface"), run.get("locale"),
            run.get("country"), run.get("device"), run.get("account_state"),
            run.get("personalization"), run.get("web_access"), run.get("panel_version"),
            session.get("context_state"), session.get("client_material_exposure"),
            session.get("documentation_status"), run.get("repeat_index"),
        )
        for observation_index, observation in enumerate(run.get("observations", [])):
            if not isinstance(observation, dict) or not isinstance(observation.get("prompt_id"), str):
                continue
            path = f"geo_runs[{index}].observations[{observation_index}]"
            slot = run_context + (observation["prompt_id"],)
            if slot in repeat_slots:
                issues.append(issue(
                    "duplicate_geo_repeat_slot", path,
                    f"Même prompt et même contexte de répétition que {repeat_slots[slot]}.",
                ))
            else:
                repeat_slots[slot] = path

    declared_geo = set(manifest.get("run_ids", {}).get("geo", []))
    actual_geo = ids.get("geo_runs", set())
    for run_id in declared_geo - actual_geo:
        issues.append(issue("missing_geo_run", "audit_manifest.json", f"Run GEO déclaré mais absent: {run_id}."))
    for run_id in actual_geo - declared_geo:
        issues.append(issue("undeclared_geo_run", "geo_runs", f"Run GEO présent mais non déclaré: {run_id}.", "warning"))

    graph = {action.get("action_id"): action.get("dependencies", []) for action in actions if action.get("action_id")}
    visiting: set[str] = set()
    visited: set[str] = set()
    def walk(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(dep in graph and walk(dep) for dep in graph.get(node, [])):
            return True
        visiting.remove(node)
        visited.add(node)
        return False
    if any(walk(node) for node in graph):
        issues.append(issue("dependency_cycle", "actions.json", "Cycle détecté dans les dépendances d'actions."))
    return issues


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--kit-root", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    results = validate_project(args.project, args.kit_root)
    if args.as_json:
        print(json.dumps({"valid": not any(item["severity"] == "error" for item in results), "issues": results}, ensure_ascii=False, indent=2))
    elif results:
        for item in results:
            print(f"{item['severity'].upper()} [{item['code']}] {item['path']}: {item['message']}")
    else:
        print("Projet valide.")
    return 1 if any(item["severity"] == "error" for item in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
