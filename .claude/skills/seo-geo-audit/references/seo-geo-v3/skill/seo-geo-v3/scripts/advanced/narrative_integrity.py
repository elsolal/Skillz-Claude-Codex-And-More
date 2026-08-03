#!/usr/bin/env python3
"""Aggregate declared narrative claim statuses from recorded GEO runs.

This script does not decide whether a claim is true. It summarizes the
accurate/inaccurate/outdated/unverifiable labels already recorded by reviewers.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from _advanced_common import CLAIM_STATUSES, csv_safe, load_geo_runs, pct, read_json, utc_now, write_json, write_text


def aggregate_claims(runs: list[dict[str, Any]], facts_path: Path | None = None) -> dict[str, Any]:
    facts: dict[str, dict[str, Any]] = {}
    if facts_path:
        facts_data = read_json(facts_path)
        if not isinstance(facts_data, dict) or not isinstance(facts_data.get("facts"), list):
            raise ValueError(f"{facts_path}: registre facts.json V3 attendu")
        facts = {str(item.get("key")): item for item in facts_data.get("facts", []) if item.get("key")}

    totals: Counter[str] = Counter()
    by_fact: dict[str, Counter[str]] = defaultdict(Counter)
    details: list[dict[str, Any]] = []
    audit_ids: set[str] = set()
    engines: set[str] = set()
    observation_count = 0

    for run in runs:
        run_id = str(run.get("run_id", "unknown"))
        audit_ids.add(str(run.get("audit_id", "unknown")))
        engine = str(run.get("engine", "unknown"))
        engines.add(engine)
        for observation in run.get("observations", []):
            observation_count += 1
            for claim in observation.get("claims", []):
                status = str(claim.get("status", "unverifiable"))
                if status not in CLAIM_STATUSES:
                    status = "unverifiable"
                fact_key = str(claim.get("fact_key") or "unknown")
                totals[status] += 1
                by_fact[fact_key][status] += 1
                details.append({
                    "audit_id": run.get("audit_id"),
                    "run_id": run_id,
                    "engine": engine,
                    "model": run.get("model"),
                    "panel_version": run.get("panel_version"),
                    "repeat_index": run.get("repeat_index"),
                    "prompt_id": observation.get("prompt_id"),
                    "prompt_text": observation.get("prompt_text"),
                    "captured_at": observation.get("captured_at"),
                    "fact_key": fact_key,
                    "status": status,
                    "notes": claim.get("notes", ""),
                })

    verifiable = totals["accurate"] + totals["inaccurate"] + totals["outdated"]
    fact_rows: list[dict[str, Any]] = []
    for key in sorted(by_fact):
        counts = by_fact[key]
        assessed = counts["accurate"] + counts["inaccurate"] + counts["outdated"]
        known = facts.get(key)
        row: dict[str, Any] = {
            "fact_key": key,
            "total": sum(counts.values()),
            "by_status": {status: counts[status] for status in CLAIM_STATUSES},
            "accuracy_pct_excluding_unverifiable": pct(counts["accurate"], assessed),
            "flagged": bool(counts["inaccurate"] or counts["outdated"]),
        }
        if known:
            row["fact_registry"] = {
                "fact_id": known.get("fact_id"),
                "status": known.get("status"),
                "confidence": known.get("confidence"),
                "valid_to": known.get("valid_to"),
            }
        fact_rows.append(row)

    limitations = [
        "Les statuts sont agrégés tels qu'enregistrés; le script ne vérifie pas lui-même la véracité des claims.",
        "Le taux d'exactitude exclut les claims unverifiable de son dénominateur et doit être lu avec leur volume.",
    ]
    if len(audit_ids) > 1:
        limitations.append("Plusieurs audit_id sont agrégés; segmenter avant d'interpréter une évolution.")
    if not details:
        limitations.append("Aucun claim enregistré dans les runs fournis.")

    return {
        "schema_version": "3.0",
        "generated_at": utc_now(),
        "method": "Aggregation of reviewer-assigned claim statuses; no truth inference is performed.",
        "audit_ids": sorted(audit_ids),
        "engines": sorted(engines),
        "run_count": len(runs),
        "observation_count": observation_count,
        "overall": {
            "claims_total": len(details),
            "by_status": {status: totals[status] for status in CLAIM_STATUSES},
            "verifiable_claims": verifiable,
            "accuracy_pct_excluding_unverifiable": pct(totals["accurate"], verifiable),
            "unverifiable_share_pct": pct(totals["unverifiable"], len(details)),
        },
        "by_fact_key": fact_rows,
        "flagged_fact_keys": [row["fact_key"] for row in fact_rows if row["flagged"]],
        "details": details,
        "limitations": limitations,
    }


def details_csv(report: dict[str, Any]) -> str:
    fields = [
        "audit_id", "run_id", "engine", "model", "panel_version", "repeat_index",
        "prompt_id", "prompt_text", "captured_at", "fact_key", "status", "notes",
    ]
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in report.get("details", []):
        writer.writerow({field: csv_safe(row.get(field)) for field in fields})
    return output.getvalue()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path, help="Projet, dossier geo_runs ou fichier(s) de run GEO")
    parser.add_argument("--facts", type=Path, help="facts.json optionnel, utilisé uniquement pour enrichir les clés")
    parser.add_argument("--output", type=Path, help="Rapport JSON; stdout si omis")
    parser.add_argument("--csv", type=Path, help="Détail plat optionnel des claims")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = aggregate_claims(load_geo_runs(args.inputs), args.facts)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"ERREUR: {exc}") from exc
    if args.output:
        write_json(args.output, report)
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.csv:
        write_text(args.csv, details_csv(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
