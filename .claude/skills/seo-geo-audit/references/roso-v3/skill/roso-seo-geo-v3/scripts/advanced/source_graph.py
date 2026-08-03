#!/usr/bin/env python3
"""Build a traceable prompt -> domain -> URL citation graph from GEO runs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from _advanced_common import csv_safe, load_geo_runs, utc_now, write_json, write_text


def _node_id(kind: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"{kind}_{digest}"


def _domain(citation: dict[str, Any]) -> str:
    declared = str(citation.get("domain") or "").strip().lower().rstrip(".")
    observed = (urlsplit(str(citation.get("url") or "")).hostname or "").lower().rstrip(".")
    return observed or declared or "unknown"


def build_graph(runs: list[dict[str, Any]], include_non_ok: bool = False) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edge_data: dict[tuple[str, str, str], dict[str, Any]] = defaultdict(lambda: {
        "count": 0, "run_ids": set(), "engines": set(), "prompt_ids": set(), "is_brand_count": 0,
    })
    paths: list[dict[str, Any]] = []
    skipped_observations = 0
    domain_mismatches = 0

    for run in runs:
        run_id = str(run.get("run_id", "unknown"))
        engine = str(run.get("engine", "unknown"))
        for observation in run.get("observations", []):
            if observation.get("response_status") != "ok" and not include_non_ok:
                skipped_observations += 1
                continue
            prompt_id = str(observation.get("prompt_id", "unknown"))
            prompt_key = f"{run.get('panel_version', '')}|{prompt_id}|{observation.get('prompt_text', '')}"
            prompt_node = _node_id("prompt", prompt_key)
            nodes[prompt_node] = {
                "id": prompt_node,
                "type": "prompt",
                "prompt_id": prompt_id,
                "label": observation.get("prompt_text") or prompt_id,
                "intent": observation.get("intent"),
                "funnel_stage": observation.get("funnel_stage"),
                "query_type": observation.get("query_type"),
                "panel_version": run.get("panel_version"),
            }
            for citation in observation.get("citations", []):
                url = str(citation.get("url") or "").strip()
                if not url:
                    continue
                domain = _domain(citation)
                declared_domain = str(citation.get("domain") or "").strip().lower().rstrip(".")
                url_domain = (urlsplit(url).hostname or "").lower().rstrip(".")
                domain_mismatch = bool(declared_domain and url_domain and declared_domain != url_domain)
                domain_mismatches += int(domain_mismatch)
                domain_node = _node_id("domain", domain)
                url_node = _node_id("url", url)
                nodes[domain_node] = {"id": domain_node, "type": "domain", "label": domain, "domain": domain}
                nodes[url_node] = {
                    "id": url_node, "type": "url", "label": citation.get("title") or url,
                    "url": url, "domain": domain,
                }
                for edge_type, source, target in (
                    ("prompt_cites_domain", prompt_node, domain_node),
                    ("domain_contains_url", domain_node, url_node),
                ):
                    edge = edge_data[(edge_type, source, target)]
                    edge["count"] += 1
                    edge["run_ids"].add(run_id)
                    edge["engines"].add(engine)
                    edge["prompt_ids"].add(prompt_id)
                    edge["is_brand_count"] += int(bool(citation.get("is_brand")))
                paths.append({
                    "audit_id": run.get("audit_id"),
                    "run_id": run_id,
                    "engine": engine,
                    "model": run.get("model"),
                    "panel_version": run.get("panel_version"),
                    "repeat_index": run.get("repeat_index"),
                    "prompt_id": prompt_id,
                    "prompt_text": observation.get("prompt_text"),
                    "intent": observation.get("intent"),
                    "funnel_stage": observation.get("funnel_stage"),
                    "query_type": observation.get("query_type"),
                    "domain": domain,
                    "declared_domain": declared_domain,
                    "domain_mismatch": domain_mismatch,
                    "url": url,
                    "title": citation.get("title", ""),
                    "is_brand": bool(citation.get("is_brand")),
                    "captured_at": observation.get("captured_at"),
                })

    edges: list[dict[str, Any]] = []
    for (edge_type, source, target), values in sorted(edge_data.items()):
        edges.append({
            "id": _node_id("edge", f"{edge_type}|{source}|{target}"),
            "type": edge_type,
            "source": source,
            "target": target,
            "citation_occurrences": values["count"],
            "brand_occurrences": values["is_brand_count"],
            "distinct_runs": len(values["run_ids"]),
            "distinct_prompts": len(values["prompt_ids"]),
            "run_ids": sorted(values["run_ids"]),
            "engines": sorted(values["engines"]),
        })

    return {
        "schema_version": "3.0",
        "generated_at": utc_now(),
        "method": "Recorded citation occurrences; repeated runs remain visible and are not deduplicated away.",
        "run_count": len(runs),
        "citation_occurrences": len(paths),
        "domain_mismatch_count": domain_mismatches,
        "skipped_non_ok_observations": skipped_observations,
        "nodes": sorted(nodes.values(), key=lambda item: (item["type"], item["id"])),
        "edges": edges,
        "paths": paths,
        "limitations": [
            "Une citation enregistrée indique une présence dans la réponse capturée, pas une causalité ni une attribution de conversion.",
            "Les répétitions sont comptées séparément; utiliser distinct_runs et distinct_prompts pour compléter le volume brut.",
        ],
    }


def paths_csv(report: dict[str, Any]) -> str:
    fields = [
        "audit_id", "run_id", "engine", "model", "panel_version", "repeat_index", "prompt_id",
        "prompt_text", "intent", "funnel_stage", "query_type", "domain", "declared_domain", "domain_mismatch",
        "url", "title", "is_brand", "captured_at",
    ]
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in report.get("paths", []):
        writer.writerow({field: csv_safe(row.get(field)) for field in fields})
    return output.getvalue()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path, help="Projet, dossier geo_runs ou fichier(s) de run")
    parser.add_argument("--json-output", type=Path, help="Graphe JSON; stdout si omis")
    parser.add_argument("--csv-output", type=Path, required=True, help="Occurrences prompt-domaine-URL en CSV")
    parser.add_argument("--include-non-ok", action="store_true", help="Inspecter aussi les observations non ok")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        graph = build_graph(load_geo_runs(args.inputs), args.include_non_ok)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"ERREUR: {exc}") from exc
    if args.json_output:
        write_json(args.json_output, graph)
    else:
        print(json.dumps(graph, ensure_ascii=False, indent=2))
    write_text(args.csv_output, paths_csv(graph))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
