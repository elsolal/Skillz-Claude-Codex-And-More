#!/usr/bin/env python3
"""Normalize exported GSC, Bing or GA4 CSV rows into V3 evidence JSONL.

This is a local file importer. It never authenticates to or calls an external API.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

from _advanced_common import read_json, utc_now, write_text


SOURCE_CONFIG = {
    "gsc": {"source_type": "search_console", "permission": "read_gsc", "label": "Google Search Console CSV"},
    "bing": {"source_type": "bing_webmaster", "permission": "read_bing", "label": "Bing Webmaster CSV"},
    "ga4": {"source_type": "ga4", "permission": "read_ga4", "label": "Google Analytics 4 CSV"},
}

DIMENSION_ALIASES = {
    "date": "date", "jour": "date",
    "query": "query", "queries": "query", "requete": "query", "requetes": "query", "grounding_query": "query",
    "page": "page", "pages": "page", "url": "page", "cited_url": "page", "cited_page": "page",
    "top_pages": "page", "landing_page": "landing_page", "landing_page_query_string": "landing_page",
    "country": "country", "pays": "country", "device": "device", "appareil": "device",
    "search_appearance": "search_appearance", "apparence_dans_les_resultats_de_recherche": "search_appearance",
    "session_source_medium": "source_medium", "source_medium": "source_medium",
    "session_default_channel_group": "channel_group", "default_channel_group": "channel_group",
    "campaign": "campaign", "session_campaign": "campaign", "event_name": "event_name",
}

METRIC_ALIASES = {
    "clicks": "clicks", "clics": "clicks", "impressions": "impressions",
    "ctr": "ctr_pct", "click_through_rate": "ctr_pct", "taux_de_clics": "ctr_pct",
    "position": "average_position", "average_position": "average_position", "avg_position": "average_position",
    "citations": "citations", "total_citations": "citations", "cited_pages": "cited_pages",
    "sessions": "sessions", "engaged_sessions": "engaged_sessions", "sessions_engagees": "engaged_sessions",
    "engagement_rate": "engagement_rate_pct", "taux_d_engagement": "engagement_rate_pct",
    "users": "users", "utilisateurs": "users", "total_users": "users", "new_users": "new_users",
    "conversions": "conversions", "key_events": "key_events", "evenements_cles": "key_events",
    "total_revenue": "revenue", "purchase_revenue": "revenue", "revenu_total": "revenue",
}


def normalize_header(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").lower().strip()
    return re.sub(r"[^a-z0-9]+", "_", value).strip("_")


def parse_number(value: str) -> tuple[int | float | None, str | None]:
    text = value.strip().replace("\u00a0", "").replace(" ", "")
    if not text:
        return None, None
    unit = "percent" if text.endswith("%") else None
    if unit:
        text = text[:-1]
    text = re.sub(r"[^0-9,\.\-+]", "", text)
    if not text or text in {"-", "+", ".", ","}:
        return None, unit
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        left, right = text.rsplit(",", 1)
        text = left + right if len(right) == 3 and left not in {"0", "+0", "-0"} else left + "." + right
    try:
        number = float(text)
    except ValueError:
        return None, unit
    if number.is_integer() and unit is None:
        return int(number), unit
    return number, unit


def _dialect(path: Path, encoding: str, delimiter: str | None) -> csv.Dialect:
    if delimiter:
        class Explicit(csv.excel):
            pass
        Explicit.delimiter = delimiter
        return Explicit()
    with path.open("r", encoding=encoding, errors="strict") as stream:
        sample = stream.read(8192)
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        return csv.excel()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_csv(
    path: Path,
    source: str,
    audit_id: str,
    collected_at: str | None = None,
    encoding: str = "utf-8-sig",
    delimiter: str | None = None,
    include_unknown: bool = False,
) -> list[dict[str, Any]]:
    config = SOURCE_CONFIG[source]
    collected_at = collected_at or utc_now()
    parsed_collected_at = dt.datetime.fromisoformat(collected_at.replace("Z", "+00:00"))
    if parsed_collected_at.tzinfo is None:
        raise ValueError("collected_at doit inclure un fuseau horaire, par exemple Z ou +02:00.")
    records: list[dict[str, Any]] = []
    dialect = _dialect(path, encoding, delimiter)
    source_file_digest = _file_sha256(path)
    with path.open("r", encoding=encoding, newline="") as stream:
        reader = csv.DictReader(stream, dialect=dialect)
        if not reader.fieldnames:
            raise ValueError("CSV sans en-tête")
        normalized_headers = [normalize_header(item or "") for item in reader.fieldnames]
        if len(normalized_headers) != len(set(normalized_headers)):
            raise ValueError("Des colonnes CSV deviennent dupliquées après normalisation de leur nom.")
        for row_number, row in enumerate(reader, 2):
            if not any(str(value or "").strip() for value in row.values()):
                continue
            dimensions: dict[str, str] = {}
            metrics: dict[str, int | float] = {}
            units: dict[str, str] = {}
            unknown: dict[str, str] = {}
            canonical_row: dict[str, str] = {}
            for original, raw_value in row.items():
                header = normalize_header(original or "")
                value = str(raw_value or "").strip()
                canonical_row[header] = value
                if not value:
                    continue
                if header in DIMENSION_ALIASES:
                    dimensions[DIMENSION_ALIASES[header]] = value
                    continue
                metric_name = METRIC_ALIASES.get(header)
                number, unit = parse_number(value)
                if metric_name and number is not None:
                    metrics[metric_name] = number
                    if unit:
                        units[metric_name] = unit
                elif include_unknown:
                    if number is not None:
                        metrics[f"other.{header}"] = number
                        if unit:
                            units[f"other.{header}"] = unit
                    else:
                        unknown[header] = value
            normalized_digest_input = json.dumps(
                {"source": source, "audit_id": audit_id, "row": canonical_row},
                ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            )
            normalized_digest = hashlib.sha256(normalized_digest_input.encode("utf-8")).hexdigest()
            identity_input = f"{source}|{audit_id}|{source_file_digest}|{row_number}"
            identity_digest = hashlib.sha256(identity_input.encode("utf-8")).hexdigest()
            metadata: dict[str, Any] = {
                "metric_source": source,
                "input_kind": "csv_export",
                "input_file": path.name,
                "row_number": row_number,
                "dimensions": dimensions,
                "metrics": metrics,
                "units": units,
                "source_file_hash": f"sha256:{source_file_digest}",
                "normalized_row_hash": f"sha256:{normalized_digest}",
            }
            if unknown:
                metadata["unmapped_fields"] = unknown
            summary = ", ".join(f"{key}={value}" for key, value in metrics.items()) or "aucune métrique reconnue"
            records.append({
                "schema_version": "3.0",
                "evidence_id": f"ev_{source}_{identity_digest[:24]}",
                "audit_id": audit_id,
                "check_id": f"metrics.{source}.csv_row",
                "collected_at": collected_at,
                "expires_at": None,
                "source_type": config["source_type"],
                "method": "file_import",
                "source_label": f"{config['label']} — {path.name}:{row_number}",
                "observation": f"Ligne importée depuis un export CSV local ({summary}).",
                "raw_hash": f"sha256:{source_file_digest}",
                "raw_path": None,
                "status": "observed",
                "confidence": "confirmed",
                "collector": "advanced/import_metrics.py",
                "authorization_permission": config["permission"],
                "metadata": metadata,
            })
    return records


def records_jsonl(records: list[dict[str, Any]]) -> str:
    return "".join(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n" for item in records)


def _existing_evidence_ids(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    ids: set[str] = set()
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{number}: JSONL invalide: {exc.msg}") from exc
        evidence_id = value.get("evidence_id") if isinstance(value, dict) else None
        if evidence_id:
            ids.add(str(evidence_id))
    return ids


def _audit_from_project(project: Path, source: str) -> str:
    manifest = read_json(project / "audit_manifest.json")
    permission = SOURCE_CONFIG[source]["permission"]
    granted = manifest.get("authorization", {}).get("permissions", [])
    if permission not in granted:
        raise PermissionError(f"Permission {permission} absente du manifeste; faire autoriser l'import avant écriture.")
    return str(manifest.get("audit_id"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Export CSV local")
    parser.add_argument("--source", choices=sorted(SOURCE_CONFIG), required=True)
    parser.add_argument("--audit-id", help="audit_id pour une sortie autonome")
    parser.add_argument("--project", type=Path, help="Projet V3; vérifie la permission correspondante")
    parser.add_argument("--output", type=Path, help="JSONL; avec --project, défaut: evidence.jsonl")
    parser.add_argument("--append", action="store_true", help="Ajouter au JSONL au lieu de le remplacer")
    parser.add_argument("--collected-at", help="Date-time ISO de collecte/import")
    parser.add_argument("--encoding", default="utf-8-sig")
    parser.add_argument("--delimiter", choices=[",", ";", "\t"])
    parser.add_argument("--include-unknown", action="store_true", help="Inclure explicitement les colonnes non reconnues")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.collected_at:
            parsed = dt.datetime.fromisoformat(args.collected_at.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                raise ValueError("--collected-at doit inclure un fuseau horaire, par exemple Z ou +02:00.")
        project = args.project.expanduser().resolve() if args.project else None
        audit_id = _audit_from_project(project, args.source) if project else args.audit_id
        if not audit_id:
            raise ValueError("Utilisez --audit-id ou --project.")
        if not str(audit_id).startswith("audit_"):
            raise ValueError("audit_id doit commencer par audit_.")
        records = normalize_csv(
            args.input.expanduser().resolve(), args.source, str(audit_id), args.collected_at, args.encoding,
            "\t" if args.delimiter == "\t" else args.delimiter, args.include_unknown,
        )
        output = (args.output.expanduser().resolve() if args.output else (project / "evidence.jsonl" if project else None))
        ledger = (project / "evidence.jsonl").resolve() if project else None
        if ledger and output and output.resolve() == ledger and not args.append:
            raise ValueError("L'écriture dans evidence.jsonl exige --append pour éviter un écrasement accidentel.")
        skipped = 0
        if output and args.append:
            existing = _existing_evidence_ids(output)
            unique_records = []
            for record in records:
                if record["evidence_id"] in existing:
                    skipped += 1
                    continue
                existing.add(record["evidence_id"])
                unique_records.append(record)
            records = unique_records
        payload = records_jsonl(records)
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            if args.append:
                with output.open("a", encoding="utf-8") as stream:
                    stream.write(payload)
            else:
                write_text(output, payload)
        else:
            sys.stdout.write(payload)
        print(
            f"{len(records)} observation(s) écrite(s), {skipped} doublon(s) ignoré(s) depuis un fichier CSV local; aucune API appelée.",
            file=sys.stderr,
        )
    except (OSError, ValueError, PermissionError, json.JSONDecodeError) as exc:
        print(f"ERREUR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
