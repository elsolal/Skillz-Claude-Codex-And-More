#!/usr/bin/env python3
"""Calculate reproducible GEO visibility metrics without inventing confidence intervals."""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from _common import pct, read_json, utc_now, write_json


PANEL_CONTEXT_FIELDS = (
    "brand_name",
    "brand_domain",
    "brand_aliases",
    "engine",
    "model",
    "surface",
    "locale",
    "country",
    "device",
    "account_state",
    "personalization",
    "web_access",
    "panel_version",
    "session_context_state",
    "session_client_material_exposure",
    "session_documentation_status",
)

SEGMENT_CONTEXT_FIELDS = PANEL_CONTEXT_FIELDS + (
    "query_type",
    "funnel_stage",
    "intent",
    "persona",
    "prompt_origin_type",
    "criticality",
)

RECOMMENDATION_EVALUABLE = {"positive", "neutral", "negative", "brand_absent"}


def load_runs(input_path: Path) -> list[dict[str, Any]]:
    if input_path.is_file():
        return [read_json(input_path)]
    geo_dir = input_path / "geo_runs" if (input_path / "geo_runs").is_dir() else input_path
    return [read_json(path) for path in sorted(geo_dir.glob("*.json"))]


def _metric_block(observations: list[dict[str, Any]]) -> dict[str, Any]:
    attempted = len(observations)
    usable = [obs for obs in observations if obs.get("response_status") == "ok"]
    mentioned = [obs for obs in usable if obs.get("brand_mentioned") is True]
    cited_prompts = [obs for obs in usable if any(c.get("is_brand") for c in obs.get("citations", []))]
    all_citations = [citation for obs in usable for citation in obs.get("citations", [])]
    brand_citations = [citation for citation in all_citations if citation.get("is_brand")]
    positions = [obs["brand_position"] for obs in mentioned if isinstance(obs.get("brand_position"), int)]
    claims = [claim for obs in usable for claim in obs.get("claims", [])]
    assessed_claims = [claim for claim in claims if claim.get("status") in {"accurate", "inaccurate", "outdated"}]
    accurate = sum(claim.get("status") == "accurate" for claim in assessed_claims)
    sentiments = Counter(obs.get("sentiment", "unrated") for obs in usable)
    recommendation_evaluable = [
        obs for obs in usable
        if obs.get("recommendation_status") in RECOMMENDATION_EVALUABLE
        and (
            (obs.get("recommendation_status") == "brand_absent" and obs.get("brand_mentioned") is False)
            or (obs.get("recommendation_status") != "brand_absent" and obs.get("brand_mentioned") is True)
        )
    ]
    positive_recommendations = sum(
        obs.get("recommendation_status") == "positive" for obs in recommendation_evaluable
    )
    inconsistent_recommendation_annotations = sum(
        obs.get("recommendation_status") in RECOMMENDATION_EVALUABLE and obs not in recommendation_evaluable
        for obs in usable
    )
    return {
        "attempted_observations": attempted,
        "usable_observations": len(usable),
        "response_success_rate_pct": pct(len(usable), attempted),
        "brand_mention_rate_pct": pct(len(mentioned), len(usable)),
        "brand_cited_prompt_rate_pct": pct(len(cited_prompts), len(usable)),
        "brand_citation_share_pct": pct(len(brand_citations), len(all_citations)),
        "brand_mentions": len(mentioned),
        "brand_citations": len(brand_citations),
        "all_citations": len(all_citations),
        "average_brand_position": round(statistics.mean(positions), 2) if positions else None,
        "narrative_accuracy_pct": pct(accurate, len(assessed_claims)),
        "claims_assessed": len(assessed_claims),
        "claims_unverifiable": sum(claim.get("status") == "unverifiable" for claim in claims),
        "positive_recommendation_rate_pct": pct(positive_recommendations, len(recommendation_evaluable)),
        "positive_recommendations": positive_recommendations,
        "recommendation_observations_evaluable": len(recommendation_evaluable),
        "recommendation_annotations_inconsistent": inconsistent_recommendation_annotations,
        "sentiment_distribution": dict(sorted(sentiments.items())),
    }


def calculate_metrics(runs: list[dict[str, Any]]) -> dict[str, Any]:
    observations: list[dict[str, Any]] = []
    by_segment_obs: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    segment_contexts: dict[tuple[str, ...], dict[str, str]] = {}
    source_domains: Counter[str] = Counter()
    competitor_mentions: Counter[str] = Counter()
    prompt_outcomes: dict[tuple[str, ...], dict[int, tuple[bool, bool]]] = defaultdict(dict)
    duplicate_repeat_slots: set[tuple[str, ...]] = set()
    repeat_groups: dict[tuple[str, ...], set[int]] = defaultdict(set)
    repeat_expected: dict[tuple[str, ...], int] = {}
    brand_signatures: set[tuple[str, str]] = set()
    panel_groups: dict[tuple[str, ...], dict[str, Any]] = {}

    for run in runs:
        brand = run.get("brand", {})
        session = run.get("session", {}) if isinstance(run.get("session"), dict) else {}
        brand_signatures.add((str(brand.get("name", "")), str(brand.get("domain", ""))))
        run_context = {
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
        }
        panel_key = tuple(run_context[field] for field in PANEL_CONTEXT_FIELDS)
        panel_group = panel_groups.setdefault(panel_key, {
            "context": run_context,
            "run_count": 0,
            "definitions": [],
            "missing_definition": False,
            "attempted_prompt_ids": set(),
            "usable_prompt_ids": set(),
        })
        panel_group["run_count"] += 1
        planned = run.get("planned_prompt_ids")
        if isinstance(planned, list) and planned and all(isinstance(value, str) and value for value in planned):
            panel_group["definitions"].append(frozenset(planned))
        else:
            panel_group["missing_definition"] = True
        for observation in run.get("observations", []):
            prompt_origin = observation.get("prompt_origin", {}) if isinstance(observation.get("prompt_origin"), dict) else {}
            context = {
                **run_context,
                "query_type": str(observation.get("query_type", "unknown")),
                "funnel_stage": str(observation.get("funnel_stage", "unknown")),
                "intent": str(observation.get("intent", "unknown")),
                "persona": str(observation.get("persona", "unknown")),
                "prompt_origin_type": str(prompt_origin.get("type", "unknown")),
                "criticality": str(observation.get("criticality", "unknown")),
            }
            segment_key = tuple(context[field] for field in SEGMENT_CONTEXT_FIELDS)
            segment_contexts[segment_key] = context
            enriched = dict(observation)
            enriched["_context"] = context
            enriched["_panel_key"] = panel_key
            observations.append(enriched)
            by_segment_obs[segment_key].append(enriched)
            prompt_id = observation.get("prompt_id")
            if isinstance(prompt_id, str) and prompt_id:
                panel_group["attempted_prompt_ids"].add(prompt_id)
                if observation.get("response_status") == "ok":
                    panel_group["usable_prompt_ids"].add(prompt_id)
            if observation.get("response_status") != "ok":
                continue
            for citation in observation.get("citations", []):
                if citation.get("domain"):
                    source_domains[str(citation["domain"]).lower()] += 1
            competitor_mentions.update(str(name) for name in observation.get("competitors_mentioned", []))
            cited = any(c.get("is_brand") for c in observation.get("citations", []))
            prompt_key = segment_key + (str(observation.get("prompt_id")),)
            repeat_index = int(run.get("repeat_index", 1))
            outcome = (bool(observation.get("brand_mentioned")), cited)
            if repeat_index in prompt_outcomes[prompt_key]:
                duplicate_repeat_slots.add(prompt_key)
            else:
                prompt_outcomes[prompt_key][repeat_index] = outcome
            repeat_key = segment_key + (str(observation.get("prompt_id")),)
            repeat_groups[repeat_key].add(repeat_index)
            repeat_expected[repeat_key] = max(repeat_expected.get(repeat_key, 1), int(run.get("total_repeats", 1)))

    inconsistent_mentions = 0
    inconsistent_citations = 0
    repeated_prompts = 0
    for outcomes_by_repeat in prompt_outcomes.values():
        outcomes = list(outcomes_by_repeat.values())
        if len(outcomes) < 2:
            continue
        repeated_prompts += 1
        if len({outcome[0] for outcome in outcomes}) > 1:
            inconsistent_mentions += 1
        if len({outcome[1] for outcome in outcomes}) > 1:
            inconsistent_citations += 1
    repeat_ratios = [len(indexes) / repeat_expected[key] for key, indexes in repeat_groups.items() if repeat_expected[key] > 0]

    limitations: list[str] = []
    if len(brand_signatures) > 1:
        limitations.append("Plusieurs identités de marque figurent dans les runs; vérifier le périmètre avant comparaison.")
    if not runs:
        limitations.append("Aucun run GEO disponible.")
    if repeat_groups and any(ratio < 1 for ratio in repeat_ratios):
        limitations.append("Le plan de répétitions est incomplet; les taux décrivent uniquement les observations disponibles.")
    if duplicate_repeat_slots:
        limitations.append(
            "Des observations dupliquées occupent le même prompt et le même numéro de répétition; "
            "elles sont exclues du décompte des répétitions distinctes et le projet doit être corrigé."
        )
    if repeated_prompts == 0 and observations:
        limitations.append("Aucun prompt n'a été répété; la volatilité n'est pas mesurable.")

    panel_contexts: list[dict[str, Any]] = []
    panel_by_key: dict[tuple[str, ...], dict[str, Any]] = {}
    for index, key in enumerate(sorted(panel_groups), 1):
        group = panel_groups[key]
        definitions = set(group["definitions"])
        if group["missing_definition"] or len(group["definitions"]) != group["run_count"]:
            status = "not_measurable_missing_plan"
            planned_ids: set[str] | None = None
        elif len(definitions) != 1:
            status = "not_measurable_inconsistent_plan"
            planned_ids = None
        else:
            status = "available"
            planned_ids = set(next(iter(definitions)))
        covered_ids = planned_ids & group["usable_prompt_ids"] if planned_ids is not None else set()
        panel_result = {
            "panel_context_id": f"panel_context_{index:03d}",
            "status": status,
            "context": group["context"],
            "run_count": group["run_count"],
            "planned_prompt_count": len(planned_ids) if planned_ids is not None else None,
            "usable_planned_prompt_count": len(covered_ids) if planned_ids is not None else None,
            "panel_coverage_pct": pct(len(covered_ids), len(planned_ids)) if planned_ids is not None else None,
            "unplanned_prompt_ids": sorted(group["attempted_prompt_ids"] - planned_ids) if planned_ids is not None else [],
        }
        panel_contexts.append(panel_result)
        panel_by_key[key] = panel_result
        if panel_result["unplanned_prompt_ids"]:
            limitations.append(
                f"{panel_result['panel_context_id']}: des prompts observés ne figurent pas dans le plan gelé; ils n'augmentent pas la couverture."
            )

    if len(panel_contexts) == 1 and panel_contexts[0]["status"] == "available":
        panel_coverage_status = "available_homogeneous_context"
        panel_coverage_pct = panel_contexts[0]["panel_coverage_pct"]
    elif not panel_contexts:
        panel_coverage_status = "no_data"
        panel_coverage_pct = None
    elif len(panel_contexts) > 1:
        panel_coverage_status = "not_reported_mixed_contexts"
        panel_coverage_pct = None
        limitations.append(
            "Aucune couverture globale du panel n'est calculée: plusieurs contextes de panel doivent être lus séparément."
        )
    else:
        panel_coverage_status = panel_contexts[0]["status"]
        panel_coverage_pct = None
        limitations.append(
            "La couverture du panel n'est pas mesurable: la liste gelée des prompts prévus est absente ou incohérente."
        )

    ordered_segment_keys = sorted(by_segment_obs)
    segments: list[dict[str, Any]] = []
    for index, key in enumerate(ordered_segment_keys, 1):
        segment_observations = by_segment_obs[key]
        metrics = _metric_block(segment_observations)
        segment_panel_keys = {observation["_panel_key"] for observation in segment_observations}
        if len(segment_panel_keys) == 1:
            panel_result = panel_by_key[next(iter(segment_panel_keys))]
            metrics["panel_coverage_pct"] = panel_result["panel_coverage_pct"]
            metrics["panel_coverage_scope"] = panel_result["panel_context_id"]
        else:
            metrics["panel_coverage_pct"] = None
            metrics["panel_coverage_scope"] = None
        segments.append({
            "segment_id": f"segment_{index:03d}",
            "context": segment_contexts[key],
            "metrics": metrics,
        })
    if observations and all(
        segment["metrics"]["positive_recommendation_rate_pct"] is None for segment in segments
    ):
        limitations.append(
            "Le taux de recommandation positive n'est pas mesurable: aucune annotation de recommandation explicite et cohérente."
        )
    if len(segments) == 1:
        overall = {
            "status": "available_homogeneous_context",
            "context_count": 1,
            "context": segments[0]["context"],
            "metrics": segments[0]["metrics"],
        }
    elif segments:
        overall = {
            "status": "not_reported_mixed_contexts",
            "context_count": len(segments),
            "context": None,
            "metrics": None,
        }
        limitations.append(
            "Aucun taux GEO global n'est calculé: les observations couvrent plusieurs contextes; lire les segments séparément."
        )
    else:
        overall = {"status": "no_data", "context_count": 0, "context": None, "metrics": None}

    facets = {
        field: sorted({segment["context"][field] for segment in segments})
        for field in SEGMENT_CONTEXT_FIELDS
    }

    return {
        "schema_version": "3.0",
        "generated_at": utc_now(),
        "method": "Descriptive metrics over recorded observations and frozen planned prompt IDs; no statistical confidence interval is inferred.",
        "run_count": len(runs),
        "brand_signatures": [{"name": name, "domain": domain} for name, domain in sorted(brand_signatures)],
        "panel_coverage_status": panel_coverage_status,
        "panel_coverage_pct": panel_coverage_pct,
        "panel_contexts": panel_contexts,
        "overall": overall,
        "segments": segments,
        "facets": facets,
        "stability": {
            "repeated_prompt_groups": repeated_prompts,
            "mention_outcome_inconsistency_pct": pct(inconsistent_mentions, repeated_prompts),
            "citation_outcome_inconsistency_pct": pct(inconsistent_citations, repeated_prompts),
            "planned_repeat_completion_pct": round(100 * statistics.mean(repeat_ratios), 1) if repeat_ratios else None,
        },
        "top_citation_domains": [{"domain": domain, "citations": count} for domain, count in source_domains.most_common(20)],
        "competitor_mentions": [{"name": name, "mentions": count} for name, count in competitor_mentions.most_common(20)],
        "inventory_note": "Citation and competitor lists are inventories across recorded segments; they are not visibility rates.",
        "limitations": limitations,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Projet, dossier geo_runs ou fichier de run")
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    metrics = calculate_metrics(load_runs(args.input))
    if args.output:
        write_json(args.output, metrics)
    else:
        print(json.dumps(metrics, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
