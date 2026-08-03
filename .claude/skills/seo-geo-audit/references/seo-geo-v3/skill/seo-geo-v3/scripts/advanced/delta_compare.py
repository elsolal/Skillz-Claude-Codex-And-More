#!/usr/bin/env python3
"""Compare two V3 score snapshots only when scope and method are compatible."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import posixpath
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from _advanced_common import load_geo_runs, read_json, utc_now, write_json


SCORE_CANDIDATES = (
    "score_v3.json", "reports/score_v3.json", "exports/score_v3.json",
    "scores_v3.json", "reports/scores_v3.json", "exports/scores_v3.json",
)
VISIBILITY_METRICS = (
    "panel_coverage_pct", "response_success_rate_pct", "brand_mention_rate_pct",
    "brand_cited_prompt_rate_pct", "brand_citation_share_pct", "average_brand_position",
    "narrative_accuracy_pct", "positive_recommendation_rate_pct",
)
SEGMENT_CONTEXT_FIELDS = (
    "brand_name", "brand_domain", "brand_aliases", "engine", "model", "surface", "locale",
    "country", "device", "account_state", "personalization", "web_access", "panel_version",
    "session_context_state", "session_client_material_exposure", "session_documentation_status",
    "query_type", "funnel_stage", "intent", "persona", "prompt_origin_type", "criticality",
)


def _parse_as_of(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("--as-of doit inclure un fuseau horaire, par exemple Z ou +02:00.")
    return parsed


def _load_or_calculate_score(project: Path, as_of: dt.datetime | None) -> tuple[dict[str, Any], str]:
    scripts_dir = Path(__file__).resolve().parent.parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    try:
        from score_v3 import calculate_scores, input_fingerprint  # type: ignore
    except ImportError as exc:
        raise FileNotFoundError("score_v3.py non importable") from exc
    expected_fingerprint = input_fingerprint(project)
    expected_as_of = (
        as_of.astimezone(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        if as_of else None
    )
    for candidate in SCORE_CANDIDATES:
        path = project / candidate
        if path.is_file():
            score = read_json(path)
            fingerprint = score.get("input_fingerprint")
            current = fingerprint == expected_fingerprint and (
                expected_as_of is None or score.get("as_of") == expected_as_of
            )
            legacy_without_requested_date = not fingerprint and expected_as_of is None
            if current or legacy_without_requested_date:
                return score, str(path)
    return calculate_scores(project, as_of), "calculated:score_v3.py"


def _geo_signature(runs: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not runs:
        return None
    methods: set[tuple[Any, ...]] = set()
    brands: set[tuple[str, str, tuple[str, ...]]] = set()
    prompts: set[tuple[str, ...]] = set()
    repeat_indexes: dict[tuple[str, str, str, int], set[int]] = defaultdict(set)
    repeat_counts: Counter[tuple[str, str, str, int, int]] = Counter()
    for run in runs:
        brand = run.get("brand", {})
        session = run.get("session", {})
        brands.add((
            str(brand.get("name", "")), str(brand.get("domain", "")).lower(),
            tuple(sorted(str(item).lower() for item in brand.get("aliases", []))),
        ))
        methods.add((
            run.get("engine"), run.get("model"), run.get("surface"), run.get("locale"), run.get("country"),
            run.get("device"), run.get("account_state"), run.get("personalization"), run.get("web_access"),
            run.get("panel_version"), tuple(sorted(str(value) for value in run.get("planned_prompt_ids", []))),
            session.get("context_state"), session.get("client_material_exposure"),
            session.get("documentation_status"), run.get("total_repeats"),
        ))
        for observation in run.get("observations", []):
            prompt_id = str(observation.get("prompt_id"))
            origin = observation.get("prompt_origin", {})
            prompts.add((
                prompt_id, str(observation.get("prompt_text")), str(observation.get("intent")),
                str(observation.get("funnel_stage")), str(observation.get("query_type")),
                str(origin.get("type")), str(origin.get("reference")), str(observation.get("persona")),
                str(observation.get("criticality")),
            ))
            coverage_key = (str(run.get("engine")), str(run.get("panel_version")), prompt_id, int(run.get("total_repeats", 1)))
            repeat_index = int(run.get("repeat_index", 1))
            repeat_indexes[coverage_key].add(repeat_index)
            repeat_counts[coverage_key + (repeat_index,)] += 1
    coverage = [
        [*key, sorted(indexes), [repeat_counts[key + (index,)] for index in sorted(indexes)]]
        for key, indexes in sorted(repeat_indexes.items())
    ]
    return {
        "methods": [list(item) for item in sorted(methods, key=repr)],
        "brands": [[name, domain, list(aliases)] for name, domain, aliases in sorted(brands)],
        "prompts": [list(item) for item in sorted(prompts)],
        "repeat_coverage": coverage,
    }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_number}: JSON invalide: {exc.msg}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number}: chaque ligne doit être un objet JSON")
        records.append(value)
    return records


def _segment_context(run: dict[str, Any], observation: dict[str, Any]) -> dict[str, str]:
    brand = run.get("brand", {}) if isinstance(run.get("brand"), dict) else {}
    session = run.get("session", {}) if isinstance(run.get("session"), dict) else {}
    origin = observation.get("prompt_origin", {}) if isinstance(observation.get("prompt_origin"), dict) else {}
    return {
        "brand_name": str(brand.get("name", "")),
        "brand_domain": str(brand.get("domain", "")),
        "brand_aliases": ",".join(sorted(str(value) for value in brand.get("aliases", []))),
        "engine": str(run.get("engine", "unknown")),
        "model": str(run.get("model", "unknown")),
        "surface": str(run.get("surface", "unknown")),
        "locale": str(run.get("locale", "unknown")),
        "country": str(run.get("country", "unknown")),
        "device": str(run.get("device", "unknown")),
        "account_state": str(run.get("account_state", "unknown")),
        "personalization": str(run.get("personalization", "unknown")),
        "web_access": str(run.get("web_access", "unknown")),
        "panel_version": str(run.get("panel_version", "unknown")),
        "session_context_state": str(session.get("context_state", "unknown")),
        "session_client_material_exposure": str(session.get("client_material_exposure", "unknown")),
        "session_documentation_status": str(session.get("documentation_status", "unavailable")),
        "query_type": str(observation.get("query_type", "unknown")),
        "funnel_stage": str(observation.get("funnel_stage", "unknown")),
        "intent": str(observation.get("intent", "unknown")),
        "persona": str(observation.get("persona", "unknown")),
        "prompt_origin_type": str(origin.get("type", "unknown")),
        "criticality": str(observation.get("criticality", "unknown")),
    }


def _segment_key(context: dict[str, Any]) -> tuple[str, ...]:
    return tuple(str(context.get(field, "unknown")) for field in SEGMENT_CONTEXT_FIELDS)


def _geo_segment_signatures(runs: list[dict[str, Any]]) -> dict[tuple[str, ...], dict[str, Any]]:
    entries: dict[tuple[str, ...], dict[str, Any]] = {}
    for run in runs:
        planned = tuple(sorted(str(value) for value in run.get("planned_prompt_ids", [])))
        repeat_index = int(run.get("repeat_index", 1))
        total_repeats = int(run.get("total_repeats", 1))
        for observation in run.get("observations", []):
            context = _segment_context(run, observation)
            key = _segment_key(context)
            entry = entries.setdefault(key, {
                "context": context,
                "planned_prompt_sets": set(),
                "prompts": set(),
                "repeat_indexes": defaultdict(set),
                "repeat_counts": Counter(),
            })
            entry["planned_prompt_sets"].add(planned)
            origin = observation.get("prompt_origin", {}) if isinstance(observation.get("prompt_origin"), dict) else {}
            prompt_id = str(observation.get("prompt_id", ""))
            entry["prompts"].add((
                prompt_id, str(observation.get("prompt_text", "")), str(observation.get("intent", "")),
                str(observation.get("funnel_stage", "")), str(observation.get("query_type", "")),
                str(origin.get("type", "")), str(origin.get("reference", "")),
                str(observation.get("persona", "")), str(observation.get("criticality", "")),
            ))
            repeat_key = (prompt_id, total_repeats)
            entry["repeat_indexes"][repeat_key].add(repeat_index)
            entry["repeat_counts"][repeat_key + (repeat_index,)] += 1

    signatures: dict[tuple[str, ...], dict[str, Any]] = {}
    for key, entry in entries.items():
        repeat_coverage = [
            [prompt_id, total, sorted(indexes), [entry["repeat_counts"][(prompt_id, total, index)] for index in sorted(indexes)]]
            for (prompt_id, total), indexes in sorted(entry["repeat_indexes"].items())
        ]
        signatures[key] = {
            "planned_prompt_sets": [list(values) for values in sorted(entry["planned_prompt_sets"])],
            "prompts": [list(values) for values in sorted(entry["prompts"])],
            "repeat_coverage": repeat_coverage,
        }
    return signatures


def _score_segments(dimension: dict[str, Any]) -> tuple[dict[tuple[str, ...], dict[str, Any]], set[tuple[str, ...]]]:
    indexed: dict[tuple[str, ...], dict[str, Any]] = {}
    duplicates: set[tuple[str, ...]] = set()
    segments = dimension.get("segments", [])
    if not isinstance(segments, list):
        return indexed, duplicates
    for segment in segments:
        if not isinstance(segment, dict) or not isinstance(segment.get("context"), dict):
            continue
        key = _segment_key(segment["context"])
        if key in indexed:
            duplicates.add(key)
            continue
        indexed[key] = segment
    return indexed, duplicates


def _visibility_segment_deltas(
    baseline: dict[str, Any],
    current: dict[str, Any],
    left: dict[str, Any],
    right: dict[str, Any],
    base_reasons: list[str],
) -> tuple[list[dict[str, Any]], list[str]]:
    left_segments, left_duplicates = _score_segments(left)
    right_segments, right_duplicates = _score_segments(right)
    left_signatures = baseline.get("geo_segment_signatures") or {}
    right_signatures = current.get("geo_segment_signatures") or {}
    dimension_reasons: list[str] = []
    if not left_segments or not right_segments:
        dimension_reasons.append("Segments V3 absents dans au moins un snapshot.")
    if set(left_segments) != set(right_segments):
        dimension_reasons.append("Contextes GEO différents; les segments non appariés sont neutralisés.")
    if left_duplicates or right_duplicates:
        dimension_reasons.append("Contexte GEO dupliqué dans au moins un score; appariement ambigu.")

    results: list[dict[str, Any]] = []
    for key in sorted(set(left_segments) | set(right_segments)):
        baseline_segment = left_segments.get(key)
        current_segment = right_segments.get(key)
        reasons = list(base_reasons)
        if baseline_segment is None:
            reasons.append("Contexte absent du baseline.")
        if current_segment is None:
            reasons.append("Contexte absent du snapshot courant.")
        if key in left_duplicates or key in right_duplicates:
            reasons.append("Contexte dupliqué; signature non appariable de façon univoque.")
        left_signature = left_signatures.get(key)
        right_signature = right_signatures.get(key)
        if left_signature is None or right_signature is None:
            reasons.append("Signature locale du panel, des prompts ou des répétitions absente.")
        elif left_signature != right_signature:
            reasons.append("Panel, prompts ou répétitions différents pour ce contexte.")
        comparable = not reasons
        left_metrics = baseline_segment.get("metrics", {}) if baseline_segment else {}
        right_metrics = current_segment.get("metrics", {}) if current_segment else {}
        context = (baseline_segment or current_segment or {}).get("context", {})
        results.append({
            "context": context,
            "comparable": comparable,
            "reasons": list(dict.fromkeys(reasons)),
            "baseline_present": baseline_segment is not None,
            "current_present": current_segment is not None,
            "metric_deltas": {
                metric: {
                    "baseline": left_metrics.get(metric),
                    "current": right_metrics.get(metric),
                    "delta": _number_delta(left_metrics.get(metric), right_metrics.get(metric), comparable),
                }
                for metric in VISIBILITY_METRICS
            },
        })
    if results and any(not segment["comparable"] for segment in results):
        dimension_reasons.append("Au moins un segment GEO n'est pas directement comparable.")
    return results, list(dict.fromkeys(dimension_reasons))


def load_snapshot(path: Path, as_of: dt.datetime | None = None) -> dict[str, Any]:
    path = path.expanduser().resolve()
    if path.is_file():
        score = read_json(path)
        return {
            "input": str(path), "score_source": str(path), "score": score, "manifest": None,
            "geo_signature": None, "geo_segment_signatures": None, "linkage_issues": [],
        }
    if not (path / "audit_manifest.json").is_file():
        raise FileNotFoundError(f"Projet ou score JSON introuvable: {path}")
    manifest = read_json(path / "audit_manifest.json")
    audit_id = manifest.get("audit_id")
    linkage_issues: list[str] = []
    evidence_path = path / "evidence.jsonl"
    if evidence_path.is_file():
        for line_number, evidence in enumerate(_read_jsonl(evidence_path), 1):
            if evidence.get("audit_id") != audit_id:
                evidence_id = evidence.get("evidence_id", "unknown")
                linkage_issues.append(
                    f"evidence.jsonl:{line_number} ({evidence_id}): audit_id ne correspond pas au manifeste."
                )
    for filename in ("facts.json", "findings.json", "actions.json"):
        artifact_path = path / filename
        if artifact_path.is_file():
            artifact = read_json(artifact_path)
            if not isinstance(artifact, dict) or artifact.get("audit_id") != audit_id:
                linkage_issues.append(f"{filename}: audit_id ne correspond pas au manifeste.")
    runs = load_geo_runs([path]) if (path / "geo_runs").is_dir() else []
    matching_runs = []
    for run in runs:
        if run.get("audit_id") != audit_id:
            linkage_issues.append(f"geo_runs/{run.get('run_id', 'unknown')}: audit_id ne correspond pas au manifeste.")
        else:
            matching_runs.append(run)
    score, source = _load_or_calculate_score(path, as_of)
    if score.get("audit_id") != audit_id:
        linkage_issues.append("Le score chargé ne correspond pas à l'audit_id du manifeste.")
    return {
        "input": str(path), "score_source": source, "score": score,
        "manifest": manifest, "geo_signature": _geo_signature(matching_runs),
        "geo_segment_signatures": _geo_segment_signatures(matching_runs),
        "linkage_issues": linkage_issues,
    }


def _url_scope(value: str) -> tuple[str, str, int | None, str, str]:
    parsed = urlsplit(str(value))
    try:
        explicit_port = parsed.port
    except ValueError:
        explicit_port = None
    port = explicit_port or ({"https": 443, "http": 80}.get(parsed.scheme.lower()))
    path = posixpath.normpath(parsed.path or "/")
    if not path.startswith("/"):
        path = "/" + path
    return parsed.scheme.lower(), (parsed.hostname or "").lower(), port, path, parsed.query


def _as_set(value: Any) -> set[str]:
    return {str(item) for item in value} if isinstance(value, list) else set()


def _url_set(value: Any) -> set[tuple[str, str, int | None, str, str]]:
    return {_url_scope(str(item)) for item in value} if isinstance(value, list) else set()


def _scope_reasons(left: dict[str, Any] | None, right: dict[str, Any] | None) -> tuple[list[str], list[str]]:
    blocking: list[str] = []
    warnings: list[str] = []
    if not left or not right:
        return ["Manifeste absent: le périmètre ne peut pas être vérifié."], warnings
    if left.get("client_id") != right.get("client_id"):
        blocking.append("client_id différent: une évolution client ne peut pas être attribuée.")
    left_scope, right_scope = left.get("scope", {}), right.get("scope", {})
    if _url_scope(str(left_scope.get("root_url", ""))) != _url_scope(str(right_scope.get("root_url", ""))):
        blocking.append("URL racine différente (schéma, domaine, port, chemin ou requête).")
    for key, label in (("locales", "locales"), ("markets", "marchés")):
        if _as_set(left_scope.get(key)) != _as_set(right_scope.get(key)):
            blocking.append(f"{label} différents.")
    if left_scope.get("vertical") != right_scope.get("vertical"):
        blocking.append("Verticale différente.")
    if left_scope.get("mode") != right_scope.get("mode"):
        blocking.append("Mode d'audit différent.")
    if left_scope.get("max_pages") != right_scope.get("max_pages"):
        blocking.append("Limite de crawl différente.")
    if _url_set(left_scope.get("include_urls")) != _url_set(right_scope.get("include_urls")):
        blocking.append("URLs incluses différentes.")
    if _as_set(left_scope.get("exclude_patterns")) != _as_set(right_scope.get("exclude_patterns")):
        blocking.append("Motifs d'exclusion différents.")
    if _as_set(left_scope.get("expected_checks")) != _as_set(right_scope.get("expected_checks")):
        blocking.append("Contrôles attendus différents.")
    left_method, right_method = left.get("methodology", {}), right.get("methodology", {})
    if left_method.get("scoring_version") != right_method.get("scoring_version"):
        blocking.append("Version de scoring différente.")
    if left_method.get("rules_snapshot_date") != right_method.get("rules_snapshot_date"):
        warnings.append("Snapshot des règles différent; documenter les changements méthodologiques intervenus.")
    return blocking, warnings


def _number_delta(left: Any, right: Any, comparable: bool) -> float | None:
    if not comparable or isinstance(left, bool) or isinstance(right, bool):
        return None
    if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
        return None
    return round(float(right) - float(left), 2)


def compare_snapshots(baseline: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    left_score, right_score = baseline["score"], current["score"]
    left_manifest, right_manifest = baseline.get("manifest"), current.get("manifest")
    blocking, warnings = _scope_reasons(left_manifest, right_manifest)
    blocking.extend(f"Baseline — {item}" for item in baseline.get("linkage_issues", []))
    blocking.extend(f"Current — {item}" for item in current.get("linkage_issues", []))
    if left_score.get("schema_version") != right_score.get("schema_version"):
        blocking.append("Version de schéma du score différente.")
    if left_score.get("principle") != right_score.get("principle"):
        blocking.append("Principe de scoring déclaré différent.")
    left_dims, right_dims = left_score.get("dimensions", {}), right_score.get("dimensions", {})
    dimensions: dict[str, Any] = {}

    for code in sorted(set(left_dims) | set(right_dims)):
        left, right = left_dims.get(code, {}), right_dims.get(code, {})
        reasons = list(blocking)
        if not left or not right:
            reasons.append("Dimension absente dans l'un des snapshots.")
        if left.get("name") != right.get("name"):
            reasons.append("Nom de dimension différent.")
        if left.get("formula") != right.get("formula") and (left.get("formula") or right.get("formula")):
            reasons.append("Formule de dimension différente.")
        if left.get("status") != "available" or right.get("status") != "available":
            reasons.append("Données insuffisantes dans au moins un snapshot.")

        if code == "F_foundations":
            left_categories = sorted(left.get("categories", {}))
            right_categories = sorted(right.get("categories", {}))
            if left_categories != right_categories:
                reasons.append("Catégories de fondation évaluées différentes.")
            if left.get("severity_penalties") != right.get("severity_penalties"):
                reasons.append("Pénalités de sévérité différentes.")
            if left.get("confidence_factors") != right.get("confidence_factors"):
                reasons.append("Facteurs de confiance différents.")
            left_weights = {key: value.get("weight") for key, value in left.get("categories", {}).items()}
            right_weights = {key: value.get("weight") for key, value in right.get("categories", {}).items()}
            if left_weights != right_weights:
                reasons.append("Pondérations des catégories de fondation différentes.")
            if left_manifest and right_manifest:
                ls, rs = left_manifest.get("scope", {}), right_manifest.get("scope", {})
                if _as_set(ls.get("expected_checks")) != _as_set(rs.get("expected_checks")):
                    reasons.append("Contrôles attendus différents.")
                if ls.get("max_pages") != rs.get("max_pages"):
                    reasons.append("Limite de crawl différente.")
        elif code == "M_measurement":
            if left.get("weights") != right.get("weights"):
                reasons.append("Pondérations de mesure différentes.")
            if left_manifest and right_manifest and _as_set(left_manifest.get("scope", {}).get("expected_checks")) != _as_set(right_manifest.get("scope", {}).get("expected_checks")):
                reasons.append("Contrôles attendus différents.")
        elif code == "E_execution":
            if left.get("weights") != right.get("weights"):
                reasons.append("Pondérations d'exécution différentes.")
        segment_deltas: list[dict[str, Any]] = []
        if code == "V_ai_visibility":
            segment_deltas, segment_reasons = _visibility_segment_deltas(
                baseline, current, left, right, reasons,
            )
            reasons.extend(segment_reasons)

        comparable = not reasons
        item: dict[str, Any] = {
            "comparable": comparable,
            "reasons": list(dict.fromkeys(reasons)),
            "baseline": {"status": left.get("status"), "score": left.get("score")},
            "current": {"status": right.get("status"), "score": right.get("score")},
            "score_delta": _number_delta(left.get("score"), right.get("score"), comparable),
        }
        if code == "V_ai_visibility":
            item["segment_deltas"] = segment_deltas
            item["metric_deltas"] = (
                segment_deltas[0]["metric_deltas"]
                if len(segment_deltas) == 1 and segment_deltas[0]["comparable"] else {}
            )
        dimensions[code] = item

    comparable_dimensions = [key for key, value in dimensions.items() if value["comparable"]]
    return {
        "schema_version": "3.0",
        "generated_at": utc_now(),
        "method": "Direct deltas are emitted only after per-dimension scope and method compatibility checks.",
        "baseline": {"input": baseline["input"], "score_source": baseline["score_source"], "audit_id": left_score.get("audit_id")},
        "current": {"input": current["input"], "score_source": current["score_source"], "audit_id": right_score.get("audit_id")},
        "scope": {
            "compatible": not blocking,
            "blocking_reasons": blocking,
            "warnings": warnings,
        },
        "directly_comparable_dimensions": comparable_dimensions,
        "dimensions": dimensions,
        "limitations": [
            "Un delta décrit une variation entre deux observations comparables; il ne prouve pas la causalité d'une action.",
            "Les changements de méthode, de panel, de périmètre ou de données disponibles sont signalés et neutralisent le delta concerné.",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path, help="Projet V3 ou fichier score_v3.json")
    parser.add_argument("current", type=Path, help="Projet V3 ou fichier score_v3.json")
    parser.add_argument("--as-of", help="Date-time ISO commune si les scores doivent être recalculés")
    parser.add_argument("--output", type=Path, help="Rapport JSON; stdout si omis")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        as_of = _parse_as_of(args.as_of) or dt.datetime.now(dt.timezone.utc)
        result = compare_snapshots(load_snapshot(args.baseline, as_of), load_snapshot(args.current, as_of))
        result["comparison_as_of"] = as_of.isoformat().replace("+00:00", "Z")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"ERREUR: {exc}") from exc
    if args.output:
        write_json(args.output, result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
