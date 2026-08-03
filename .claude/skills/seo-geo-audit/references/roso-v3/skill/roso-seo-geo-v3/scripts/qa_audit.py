#!/usr/bin/env python3
"""Run deterministic QA gates before a RosoAI V3 audit is delivered."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from _common import delivery_payload_errors, load_simple_yaml, parse_datetime, read_json, read_jsonl, utc_now, write_json
from score_v3 import canonical_score_errors, input_fingerprint
from validate_project import validate_project


PLACEHOLDER_RE = re.compile(r"\{\{[^}]+\}\}|" + r"\[" + r"TODO[^]]*\]|\b(?:À compléter|À renseigner)\b", re.IGNORECASE)
SECRET_RE = re.compile(r"(?i)(?:api[_-]?key|password|passwd|client[_-]?secret|access[_-]?token)\s*[:=]\s*['\"]?([^\s,'\"]+)")


def qa_item(gate: str, severity: str, path: str, message: str) -> dict[str, str]:
    return {"gate": gate, "severity": severity, "path": path, "message": message}


def _event_at_or_after(event: dict[str, Any], *floors: Any) -> bool:
    try:
        event_at = parse_datetime(event.get("at"))
        parsed_floors = [parse_datetime(value) for value in floors]
    except (TypeError, ValueError):
        return False
    return (
        all(event_at >= floor for floor in parsed_floors)
        and event_at <= dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=5)
    )


def _report_validation_is_active(
    events: list[dict[str, Any]],
    validation_index: int,
    artifact: str,
) -> bool:
    """Return false when a later append-only event revoked this report validation."""

    validation = events[validation_index]
    object_id = validation.get("object_id")
    revoking_types = {"rejected", "deleted", "rolled_back"}
    for later in events[validation_index + 1:]:
        revoking_status = str(later.get("to_status") or "").lower() in revoking_types
        if (
            later.get("object_type") != "report"
            or (later.get("event_type") not in revoking_types and not revoking_status)
        ):
            continue
        later_artifacts = {
            Path(value).as_posix() for value in later.get("artifacts", []) if isinstance(value, str)
        }
        if (object_id and later.get("object_id") == object_id) or artifact in later_artifacts:
            return False
    return True


def _pdf_last_trailer(payload: bytes) -> bytes | None:
    offset = payload.rfind(b"trailer")
    if offset < 0:
        return None
    match = re.match(
        rb"trailer\s*<<(.*?)>>\s*startxref\s*\d+\s*%%EOF\s*$",
        payload[offset:],
        re.DOTALL,
    )
    return match.group(1) if match else None


def _pdf_reference(dictionary: bytes | None, key: bytes) -> tuple[int, int] | None:
    if dictionary is None:
        return None
    match = re.search(rb"/" + re.escape(key) + rb"\s+(\d+)\s+(\d+)\s+R\b", dictionary)
    return (int(match.group(1)), int(match.group(2))) if match else None


def _pdf_indirect_object(payload: bytes, reference: tuple[int, int] | None) -> bytes | None:
    if reference is None:
        return None
    number, generation = reference
    pattern = re.compile(
        rb"(?m)^[ \t]*" + str(number).encode("ascii") + rb"\s+"
        + str(generation).encode("ascii") + rb"\s+obj\b"
    )
    matches = list(pattern.finditer(payload))
    if not matches:
        return None
    start = matches[-1].end()
    end = payload.find(b"endobj", start)
    return payload[start:end] if end >= 0 else None


def _pdf_string_token(dictionary: bytes | None, key: bytes) -> bytes | None:
    if dictionary is None:
        return None
    match = re.search(rb"/" + re.escape(key) + rb"(?![A-Za-z0-9])", dictionary)
    if not match:
        return None
    index = match.end()
    while index < len(dictionary) and dictionary[index] in b" \t\r\n\f\x00":
        index += 1
    if index >= len(dictionary):
        return None
    if dictionary[index] == ord("<") and dictionary[index:index + 2] != b"<<":
        end = dictionary.find(b">", index + 1)
        return dictionary[index:end + 1] if end >= 0 else None
    if dictionary[index] != ord("("):
        return None
    start = index
    depth = 0
    while index < len(dictionary):
        byte = dictionary[index]
        if byte == ord("\\"):
            index += 2
            continue
        if byte == ord("("):
            depth += 1
        elif byte == ord(")"):
            depth -= 1
            if depth == 0:
                return dictionary[start:index + 1]
        index += 1
    return None


def _decode_pdf_string(token: bytes | None) -> str | None:
    if not token:
        return None
    if token.startswith(b"<"):
        compact = re.sub(rb"\s+", b"", token[1:-1])
        if not compact:
            return ""
        if len(compact) % 2:
            compact += b"0"
        try:
            decoded = bytes.fromhex(compact.decode("ascii"))
        except (UnicodeDecodeError, ValueError):
            return None
    else:
        source = token[1:-1]
        output = bytearray()
        index = 0
        escapes = {ord("n"): 0x0A, ord("r"): 0x0D, ord("t"): 0x09, ord("b"): 0x08, ord("f"): 0x0C}
        while index < len(source):
            byte = source[index]
            if byte != ord("\\"):
                output.append(byte)
                index += 1
                continue
            index += 1
            if index >= len(source):
                break
            escaped = source[index]
            if escaped in b"\r\n":
                if escaped == ord("\r") and index + 1 < len(source) and source[index + 1] == ord("\n"):
                    index += 1
                index += 1
                continue
            if escaped in b"01234567":
                end = index + 1
                while end < min(index + 3, len(source)) and source[end] in b"01234567":
                    end += 1
                output.append(int(source[index:end], 8))
                index = end
                continue
            output.append(escapes.get(escaped, escaped))
            index += 1
        decoded = bytes(output)
    try:
        if decoded.startswith(b"\xfe\xff"):
            return decoded[2:].decode("utf-16-be")
        if decoded.startswith(b"\xff\xfe"):
            return decoded[2:].decode("utf-16-le")
        return decoded.decode("latin-1")
    except UnicodeDecodeError:
        return None


def _pdf_string_field(dictionary: bytes | None, key: bytes) -> str | None:
    return _decode_pdf_string(_pdf_string_token(dictionary, key))


def pdf_page_count(path: Path) -> int | None:
    """Read the declared page count through the final trailer, catalog and Pages tree root."""

    try:
        payload = path.read_bytes()
    except OSError:
        return None
    trailer = _pdf_last_trailer(payload)
    catalog = _pdf_indirect_object(payload, _pdf_reference(trailer, b"Root"))
    pages = _pdf_indirect_object(payload, _pdf_reference(catalog, b"Pages"))
    if pages is None:
        return None
    match = re.search(rb"/Count\s+(\d+)\b", pages)
    if not match:
        return None
    count = int(match.group(1))
    return count if count > 0 else None


def inspect_pdf(path: Path) -> tuple[list[str], list[str]]:
    """Return structural blockers and metadata/accessibility warnings without optional tools."""
    try:
        payload = path.read_bytes()
    except OSError as exc:
        return [f"PDF illisible: {exc}."], []
    blockers: list[str] = []
    warnings: list[str] = []
    if len(payload) < 1024:
        blockers.append("PDF anormalement petit (moins de 1 Kio).")
    if not payload.startswith(b"%PDF-"):
        blockers.append("En-tête PDF absent ou invalide.")
    if b"%%EOF" not in payload[-4096:]:
        blockers.append("Marqueur de fin PDF absent.")
    trailer = _pdf_last_trailer(payload)
    info = _pdf_indirect_object(payload, _pdf_reference(trailer, b"Info"))
    catalog = _pdf_indirect_object(payload, _pdf_reference(trailer, b"Root"))
    for key, label in (
        (b"Title", "titre de document"),
        (b"Author", "auteur ou organisation"),
        (b"Subject", "sujet du document"),
    ):
        value = _pdf_string_field(info, key)
        if value is None or not value.strip():
            warnings.append(f"{label} absent ou vide dans le dictionnaire Info du PDF.")
    keywords = _pdf_string_field(info, b"Keywords")
    if keywords is None or not re.search(
        r"\bversion\s*[:=]?\s*v?\d+\.\d+(?:\.\d+)?(?:[-+][0-9A-Za-z.-]+)?\b",
        keywords,
        re.IGNORECASE,
    ):
        warnings.append("version de méthode absente des mots-clés du dictionnaire Info du PDF.")
    for key, label in ((b"CreationDate", "date de création"), (b"ModDate", "date de modification")):
        value = _pdf_string_field(info, key)
        if value is None or not re.fullmatch(r"D:\d{14}(?:Z|[+-]\d{2}'?\d{2}'?)?", value.strip()):
            warnings.append(f"{label} PDF absente ou invalide dans le dictionnaire Info.")
    language = _pdf_string_field(catalog, b"Lang")
    if language is None or not re.fullmatch(r"[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*", language.strip()):
        warnings.append("langue de document absente ou invalide dans le catalogue PDF.")
    if catalog is None or not re.search(rb"/StructTreeRoot\s+\d+\s+\d+\s+R\b", catalog):
        warnings.append("arborescence de structure non détectée dans le catalogue PDF.")
    if catalog is None or not re.search(rb"/MarkInfo\s*<<.*?/Marked\s+true\b.*?>>", catalog, re.DOTALL):
        warnings.append("indicateur PDF balisé non détecté dans le catalogue PDF.")
    return blockers, warnings


def run_qa(
    project: Path,
    kit_root: Path | None = None,
    as_of: dt.datetime | None = None,
    delivery: bool = False,
) -> dict[str, Any]:
    project = project.resolve()
    as_of = as_of or dt.datetime.now(dt.timezone.utc)
    items: list[dict[str, str]] = []
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        items.append(qa_item("as_of", "blocker", "--as-of", "Le fuseau horaire est obligatoire (Z ou décalage explicite)."))
        return _qa_result(items)
    try:
        validations = validate_project(project, kit_root)
    except Exception as exc:  # defensive gate: malformed client data must never crash QA
        validations = []
        items.append(qa_item("schema_and_references", "blocker", str(project), f"Validation interrompue: {exc}"))
    for validation in validations:
        severity = "blocker" if validation["severity"] == "error" else "warning"
        items.append(qa_item("schema_and_references", severity, validation["path"], validation["message"]))

    try:
        manifest = read_json(project / "audit_manifest.json")
        evidence = read_jsonl(project / "evidence.jsonl")
        facts = read_json(project / "facts.json").get("facts", [])
        findings = read_json(project / "findings.json").get("findings", [])
        actions = read_json(project / "actions.json").get("actions", [])
        events = read_jsonl(project / "events.jsonl")
        client = load_simple_yaml(project / "client.yaml")
    except Exception as exc:
        items.append(qa_item("load", "blocker", str(project), f"QA interrompue: {exc}"))
        return _qa_result(items)

    final_state = manifest.get("status") in {"qa_ready", "complete"}
    strict_delivery = delivery or final_state
    if delivery and not final_state:
        items.append(qa_item(
            "delivery_state",
            "blocker",
            "audit_manifest.json",
            f"Statut {manifest.get('status')} non livrable; utiliser qa_ready ou complete.",
        ))
    text_files = [project / "client.yaml", project / "audit_manifest.json", project / "facts.json", project / "findings.json", project / "actions.json"]
    text_files.extend((project / "reports").glob("*.md") if (project / "reports").is_dir() else [])
    for path in text_files:
        if not path.is_file():
            continue
        matches = sorted(set(match.group(0) for match in PLACEHOLDER_RE.finditer(path.read_text(encoding="utf-8"))))
        if matches:
            severity = "blocker" if strict_delivery else "warning"
            items.append(qa_item("placeholders", severity, str(path.relative_to(project)), f"Valeurs provisoires détectées: {', '.join(matches[:5])}."))

    stale_ids: list[str] = []
    for record in evidence:
        expires = record.get("expires_at")
        if expires:
            try:
                if parse_datetime(expires) < as_of:
                    stale_ids.append(record.get("evidence_id", "inconnue"))
            except (TypeError, ValueError):
                pass
        raw_path = record.get("raw_path")
        if raw_path:
            raw_file = (project / raw_path).resolve()
            try:
                raw_file.relative_to(project)
                safe_path = True
            except ValueError:
                safe_path = False
                items.append(qa_item("raw_evidence", "blocker", "evidence.jsonl", f"Chemin de capture hors projet pour {record.get('evidence_id')}: {raw_path}."))
            if safe_path and not raw_file.is_file():
                items.append(qa_item("raw_evidence", "warning", "evidence.jsonl", f"Capture brute absente pour {record.get('evidence_id')}: {raw_path}."))
            elif safe_path and record.get("raw_hash"):
                actual_hash = "sha256:" + hashlib.sha256(raw_file.read_bytes()).hexdigest()
                if actual_hash != record["raw_hash"]:
                    items.append(qa_item("raw_evidence", "blocker", "evidence.jsonl", f"Hash de capture incohérent pour {record.get('evidence_id')}: {raw_path}."))
    if stale_ids:
        severity = "blocker" if strict_delivery else "warning"
        items.append(qa_item("freshness", severity, "evidence.jsonl", f"Preuves expirées: {', '.join(stale_ids[:20])}."))

    fact_by_id = {fact.get("fact_id"): fact for fact in facts}
    finding_by_id = {finding.get("finding_id"): finding for finding in findings}
    for finding in findings:
        if finding.get("basis") in {"inferred", "proxy"} and finding.get("confidence") == "confirmed":
            items.append(qa_item("confidence", "blocker", "findings.json", f"{finding.get('finding_id')} est inféré/proxy mais marqué confirmé."))
        if finding.get("severity") in {"critical", "high"} and finding.get("confidence") == "weak":
            items.append(qa_item("confidence", "warning", "findings.json", f"{finding.get('finding_id')} est prioritaire avec une confiance faible."))
        for fact_id in finding.get("fact_ids", []):
            if fact_by_id.get(fact_id, {}).get("status") in {"conflicted", "expired", "unknown"}:
                items.append(qa_item("fact_integrity", "blocker", "findings.json", f"{finding.get('finding_id')} dépend du fait non fiable {fact_id}."))

    approval_policy = manifest.get("authorization", {}).get("write_actions_require_approval") is True
    write_permissions = set(manifest.get("authorization", {}).get("permissions", [])) & {"write_cms", "write_external"}
    for action in actions:
        if approval_policy and action.get("automation") in {"assisted", "automated"} and not action.get("approval_required"):
            items.append(qa_item("approval", "blocker", "actions.json", f"{action.get('action_id')} contourne la validation humaine requise."))
        if action.get("status") in {"in_progress", "in_review", "done"} and action.get("automation") == "automated" and not write_permissions:
            items.append(qa_item("authorization", "blocker", "actions.json", f"{action.get('action_id')} est automatisée sans permission d'écriture."))
        if action.get("status") == "done":
            action_events = [event for event in events if event.get("object_id") == action.get("action_id")]
            if not any(event.get("event_type") in {"validated", "published"} for event in action_events):
                items.append(qa_item("done_validation", "warning", "events.jsonl", f"Action terminée sans événement de validation: {action.get('action_id')}."))

    for jsonld in list(project.rglob("*.jsonld")):
        try:
            value = json.loads(jsonld.read_text(encoding="utf-8"))
            nodes = value if isinstance(value, list) else [value]
            if not all(isinstance(node, dict) and ("@type" in node or "@graph" in node) for node in nodes):
                items.append(qa_item("jsonld", "warning", str(jsonld.relative_to(project)), "JSON valide mais aucun @type/@graph explicite."))
        except (OSError, json.JSONDecodeError) as exc:
            items.append(qa_item("jsonld", "blocker", str(jsonld.relative_to(project)), f"JSON-LD invalide: {exc}."))

    for path in project.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".json", ".jsonl", ".yaml", ".yml", ".md", ".txt"}:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for match in SECRET_RE.finditer(content):
            value = match.group(1)
            if value.lower() not in {"none", "null", "xxx", "placeholder", "reference_only", "not_stored"} and not value.startswith("À"):
                items.append(qa_item("secrets", "blocker", str(path.relative_to(project)), "Secret potentiel stocké en clair."))
                break

    expected = set(manifest.get("scope", {}).get("expected_checks", []))
    observed = {record.get("check_id") for record in evidence if record.get("check_id") and record.get("status") in {"observed", "proxy", "client_reported"}}
    missing = sorted(expected - observed)
    if missing:
        severity = "blocker" if strict_delivery else "warning"
        items.append(qa_item("coverage", severity, "audit_manifest.json", f"Contrôles attendus sans preuve: {', '.join(missing)}."))

    if strict_delivery:
        current_fingerprint = input_fingerprint(project)
        expected_as_of = as_of.astimezone(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        canonical_score_path = project / "reports" / "score_v3.json"
        canonical_score_hash: str | None = None
        canonical_score_generated_at: str | None = None
        if not canonical_score_path.is_file():
            items.append(qa_item(
                "score_provenance", "blocker", "reports/score_v3.json",
                "Score canonique absent; impossible de vérifier la date et les données des livrables.",
            ))
        else:
            try:
                canonical_score = read_json(canonical_score_path)
                canonical_score_hash = "sha256:" + hashlib.sha256(canonical_score_path.read_bytes()).hexdigest()
            except (OSError, json.JSONDecodeError) as exc:
                items.append(qa_item(
                    "score_provenance", "blocker", "reports/score_v3.json",
                    f"Score canonique illisible: {exc}.",
                ))
            else:
                if not isinstance(canonical_score, dict):
                    items.append(qa_item(
                        "score_provenance", "blocker", "reports/score_v3.json",
                        "Le score canonique doit être un objet JSON.",
                    ))
                else:
                    canonical_score_generated_at = canonical_score.get("generated_at")
                    for message in canonical_score_errors(project, canonical_score, as_of):
                        items.append(qa_item(
                            "score_provenance", "blocker", "reports/score_v3.json", message,
                        ))
                    if canonical_score.get("audit_id") != manifest.get("audit_id"):
                        items.append(qa_item(
                            "score_provenance", "blocker", "reports/score_v3.json",
                            "Le score canonique appartient à un autre audit.",
                        ))
                    if canonical_score.get("input_fingerprint") != current_fingerprint:
                        items.append(qa_item(
                            "score_provenance", "blocker", "reports/score_v3.json",
                            "Le score canonique ne correspond plus aux entrées structurées courantes.",
                        ))
                    if canonical_score.get("as_of") != expected_as_of:
                        items.append(qa_item(
                            "score_provenance", "blocker", "reports/score_v3.json",
                            f"Date de coupure du score différente de la QA ({expected_as_of}).",
                        ))

        outputs = manifest.get("outputs")
        if not isinstance(outputs, list) or not outputs:
            items.append(qa_item(
                "outputs", "blocker", "audit_manifest.json",
                "Une livraison doit déclarer au moins un livrable dans outputs.",
            ))
            outputs = []
        for relative in outputs:
            output_path = (project / relative).resolve()
            try:
                output_path.relative_to(project)
            except ValueError:
                items.append(qa_item("outputs", "blocker", "audit_manifest.json", f"Sortie hors projet: {relative}."))
                continue
            if not output_path.is_file():
                items.append(qa_item("outputs", "blocker", "audit_manifest.json", f"Sortie déclarée absente: {relative}."))
                continue
            for message in delivery_payload_errors(output_path):
                items.append(qa_item("output_integrity", "blocker", relative, message))
            normalized_relative = Path(relative).as_posix()
            actual_output_hash = "sha256:" + hashlib.sha256(output_path.read_bytes()).hexdigest()
            artifact_events = [
                event for event_index, event in enumerate(events)
                if event.get("event_type") == "validated"
                and event.get("object_type") == "report"
                and normalized_relative in {
                    Path(value).as_posix() for value in event.get("artifacts", []) if isinstance(value, str)
                }
                and event.get("metadata", {}).get("sha256") == actual_output_hash
                and event.get("metadata", {}).get("input_fingerprint") == current_fingerprint
                and event.get("metadata", {}).get("score_as_of") == expected_as_of
                and event.get("metadata", {}).get("score_sha256") == canonical_score_hash
                and _event_at_or_after(
                    event, manifest.get("created_at"), canonical_score_generated_at,
                )
                and _report_validation_is_active(events, event_index, normalized_relative)
            ]
            if not artifact_events:
                items.append(qa_item(
                    "artifact_provenance",
                    "blocker",
                    relative,
                    "Aucune validation append-only ne lie le livrable aux entrées, à la date de coupure et au score canonique courants.",
                ))
            if output_path.suffix.lower() == ".pdf":
                blockers, warnings = inspect_pdf(output_path)
                actual_page_count = pdf_page_count(output_path)
                if actual_page_count is None:
                    blockers.append("Nombre de pages PDF introuvable ou invalide dans l’arbre /Pages.")
                for message in blockers:
                    items.append(qa_item("pdf_structure", "blocker", relative, message))
                for message in warnings:
                    items.append(qa_item("pdf_accessibility", "blocker", relative, message))
                reviewed = any(
                    event.get("metadata", {}).get("rendered_page_review") == "all_pages"
                    and event.get("metadata", {}).get("page_count") == actual_page_count
                    for event in artifact_events
                )
                if not reviewed:
                    items.append(qa_item(
                        "pdf_review",
                        "blocker",
                        relative,
                        "Aucune validation append-only ne lie l’inspection de toutes les pages au PDF courant et à ses entrées structurées.",
                    ))

        audit_transitions = [
            event for event in events
            if event.get("object_type") == "audit" and event.get("object_id") == manifest.get("audit_id") and event.get("to_status")
        ]
        if not audit_transitions:
            items.append(qa_item("state_history", "blocker", "events.jsonl", "Aucune transition d’état de l’audit n’est journalisée."))
        elif audit_transitions[-1].get("to_status") != manifest.get("status"):
            items.append(qa_item(
                "state_history",
                "blocker",
                "events.jsonl",
                f"Dernier état journalisé {audit_transitions[-1].get('to_status')} différent du manifest {manifest.get('status')}.",
            ))

        if manifest.get("scope", {}).get("mode") == "full":
            prefixes = {check.split(".", 1)[0] for check in expected}
            required_groups = {
                "technical": {"homepage", "robots", "sitemap", "crawl", "index", "canonical", "hreflang", "performance"},
                "content_or_demand": {"content", "keyword", "demand"},
                "entity": {"structured_data", "entity"},
                "geo": {"geo"},
            }
            if manifest.get("scope", {}).get("vertical") == "local":
                required_groups["local"] = {"local", "gbp"}
            absent_groups = [name for name, choices in required_groups.items() if not prefixes & choices]
            if absent_groups:
                items.append(qa_item(
                    "full_scope",
                    "blocker",
                    "audit_manifest.json",
                    "Mode full sans familles de contrôles attendues: " + ", ".join(absent_groups) + ".",
                ))
    if not findings:
        items.append(qa_item("findings", "warning", "findings.json", "Aucun constat enregistré; vérifier que l'analyse a bien été menée."))
    if findings and not actions:
        items.append(qa_item("actions", "blocker", "actions.json", "Des constats existent mais aucune action n'est définie."))
    return _qa_result(items)


def _qa_result(items: list[dict[str, str]]) -> dict[str, Any]:
    counts = {severity: sum(item["severity"] == severity for item in items) for severity in ("blocker", "warning", "info")}
    return {"schema_version": "3.0", "generated_at": utc_now(), "passed": counts["blocker"] == 0, "counts": counts, "items": items}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--kit-root", type=Path)
    parser.add_argument("--as-of")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--delivery", action="store_true", help="Appliquer les gates strictes de livraison")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        as_of = parse_datetime(args.as_of) if args.as_of else None
    except (TypeError, ValueError) as exc:
        print(json.dumps({"error": f"--as-of invalide: {exc}"}, ensure_ascii=False, indent=2))
        return 2
    result = run_qa(
        args.project,
        args.kit_root,
        as_of,
        delivery=args.delivery,
    )
    if args.output:
        write_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
