#!/usr/bin/env python3
"""Produce transparent, separated V3 scores from evidence-backed project data."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from _common import parse_datetime, pct, read_json, read_jsonl, utc_now, write_json
from geo_metrics import calculate_metrics, load_runs


SEVERITY_PENALTY = {"critical": 20.0, "high": 10.0, "medium": 4.0, "low": 1.0, "info": 0.0}
CONFIDENCE_FACTOR = {"confirmed": 1.0, "strong": 0.85, "moderate": 0.65, "weak": 0.4}
FOUNDATION_WEIGHTS = {"technical": 30, "content": 25, "entity": 15, "authority": 15, "local": 15}
ACTION_PROGRESS = {"backlog": 0.0, "ready": 0.1, "in_progress": 0.5, "in_review": 0.8, "done": 1.0, "blocked": 0.0}
OPPORTUNITY_WEIGHTS = {
    "opportunity.demand_score_pct": 30,
    "opportunity.business_value_score_pct": 30,
    "opportunity.content_gap_score_pct": 20,
    "opportunity.feasibility_score_pct": 20,
}
RELIABLE_FACT_STATUSES = {"client_approved", "observed"}
MEASURED_EVIDENCE_STATUSES = {"observed", "proxy", "client_reported"}


def input_fingerprint(project: Path) -> str:
    """Hash all structured scoring inputs, independent of filesystem metadata."""
    paths = [
        project / "client.yaml", project / "audit_manifest.json", project / "evidence.jsonl", project / "facts.json",
        project / "findings.json", project / "actions.json",
        *sorted((project / "geo_runs").glob("*.json")),
    ]
    digest = hashlib.sha256()
    for path in paths:
        relative = path.relative_to(project).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        if not path.is_file():
            digest.update(b"\x00MISSING")
            continue
        payload = path.read_bytes()
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return "sha256:" + digest.hexdigest()


def _check_category(check_id: str) -> str | None:
    prefix = check_id.split(".", 1)[0]
    return {
        "homepage": "technical", "robots": "technical", "sitemap": "technical", "canonical": "technical",
        "crawl": "technical", "index": "technical", "performance": "technical", "hreflang": "technical",
        "content": "content", "keyword": "content", "structured_data": "entity", "entity": "entity",
        "authority": "authority", "backlink": "authority", "local": "local", "gbp": "local",
    }.get(prefix)


def calculate_scores(project: Path, as_of: dt.datetime | None = None) -> dict[str, Any]:
    as_of = as_of or dt.datetime.now(dt.timezone.utc)
    manifest = read_json(project / "audit_manifest.json")
    evidence = read_jsonl(project / "evidence.jsonl")
    findings = read_json(project / "findings.json").get("findings", [])
    actions = read_json(project / "actions.json").get("actions", [])
    facts = read_json(project / "facts.json").get("facts", [])
    runs = load_runs(project)
    geo = calculate_metrics(runs)

    expected = set(manifest.get("scope", {}).get("expected_checks", []))
    measured_evidence = [record for record in evidence if record.get("status") in MEASURED_EVIDENCE_STATUSES]
    observed = {record.get("check_id") for record in measured_evidence if record.get("check_id")}
    confidence_values = [CONFIDENCE_FACTOR.get(record.get("confidence"), 0.0) for record in measured_evidence]
    fresh = 0
    for record in measured_evidence:
        expires_at = record.get("expires_at")
        try:
            is_fresh = not expires_at or parse_datetime(expires_at) >= as_of
        except (TypeError, ValueError):
            is_fresh = False
        fresh += int(is_fresh)

    coverage_score = pct(len(expected & observed), len(expected))
    evidence_confidence = round(100 * statistics.mean(confidence_values), 1) if confidence_values else None
    freshness_score = pct(fresh, len(measured_evidence))
    reproducibility_score = geo.get("stability", {}).get("planned_repeat_completion_pct")
    measurement_components = {
        "expected_check_coverage_pct": coverage_score,
        "evidence_confidence_pct": evidence_confidence,
        "evidence_freshness_pct": freshness_score,
        "geo_repeat_completion_pct": reproducibility_score,
    }
    component_weights = {
        "expected_check_coverage_pct": 40,
        "evidence_confidence_pct": 30,
        "evidence_freshness_pct": 20,
        "geo_repeat_completion_pct": 10,
    }
    available = [(measurement_components[key], weight) for key, weight in component_weights.items() if measurement_components[key] is not None]
    measurement_raw_score = round(sum(value * weight for value, weight in available) / sum(weight for _, weight in available), 1) if available else None
    measurement_coverage = round(100 * sum(weight for _, weight in available) / sum(component_weights.values()), 1)
    measurement_publishable = measurement_raw_score is not None and measurement_coverage >= 50
    measurement_score = measurement_raw_score if measurement_publishable else None
    measurement_confidence = (
        round((measurement_coverage / 100) * evidence_confidence, 1)
        if evidence_confidence is not None else None
    )

    assessed_categories: set[str] = set()
    for record in measured_evidence:
        if record.get("check_id"):
            category = _check_category(record["check_id"])
            if category:
                assessed_categories.add(category)
    assessed_categories.update(finding.get("category") for finding in findings if finding.get("category") in FOUNDATION_WEIGHTS)
    deductions: dict[str, float] = defaultdict(float)
    open_findings = [finding for finding in findings if finding.get("status") in {"open", "accepted", "in_progress", "blocked"}]
    for finding in open_findings:
        category = finding.get("category")
        if category not in FOUNDATION_WEIGHTS:
            continue
        deductions[category] += SEVERITY_PENALTY.get(finding.get("severity"), 0) * CONFIDENCE_FACTOR.get(finding.get("confidence"), 0)
    category_scores = {
        category: {
            "score": round(max(0.0, 100.0 - deductions[category]), 1),
            "deduction": round(deductions[category], 1),
            "open_findings": sum(finding.get("category") == category for finding in open_findings),
            "weight": FOUNDATION_WEIGHTS[category],
        }
        for category in FOUNDATION_WEIGHTS if category in assessed_categories
    }
    foundation_weight_sum = sum(FOUNDATION_WEIGHTS[category] for category in category_scores)
    foundation_raw_score = (
        round(sum(item["score"] * item["weight"] for item in category_scores.values()) / foundation_weight_sum, 1)
        if foundation_weight_sum else None
    )
    foundation_expected = {check for check in expected if _check_category(check) in FOUNDATION_WEIGHTS}
    foundation_observed = foundation_expected & observed
    foundation_coverage = pct(len(foundation_observed), len(foundation_expected))
    foundation_evidence_confidence = [
        CONFIDENCE_FACTOR.get(record.get("confidence"), 0.0)
        for record in measured_evidence if record.get("check_id") and _check_category(record["check_id"]) in FOUNDATION_WEIGHTS
    ]
    foundation_evidence_quality = round(100 * statistics.mean(foundation_evidence_confidence), 1) if foundation_evidence_confidence else None
    foundation_confidence = (
        round((foundation_coverage / 100) * foundation_evidence_quality, 1)
        if foundation_coverage is not None and foundation_evidence_quality is not None else None
    )
    foundation_publishable = foundation_raw_score is not None and foundation_coverage is not None and foundation_coverage >= 50
    foundation_score = foundation_raw_score if foundation_publishable else None

    active_actions = [action for action in actions if action.get("status") != "cancelled"]
    progress_score = (
        round(100 * statistics.mean(ACTION_PROGRESS.get(action.get("status"), 0.0) for action in active_actions), 1)
        if active_actions else None
    )
    ownership_score = pct(sum(bool(action.get("owner")) for action in active_actions), len(active_actions))
    due_date_score = pct(sum(bool(action.get("due_date")) for action in active_actions), len(active_actions))
    acceptance_score = pct(sum(bool(action.get("acceptance_criteria")) and bool(action.get("validation_method")) and bool(action.get("rollback")) for action in active_actions), len(active_actions))
    execution_parts = [(progress_score, 50), (ownership_score, 20), (due_date_score, 15), (acceptance_score, 15)]
    execution_available = [(value, weight) for value, weight in execution_parts if value is not None]
    execution_score = round(sum(value * weight for value, weight in execution_available) / sum(weight for _, weight in execution_available), 1) if execution_available else None
    execution_coverage = 100.0 if active_actions else None
    action_confidences = [CONFIDENCE_FACTOR.get(action.get("confidence"), 0.0) for action in active_actions]
    execution_evidence_quality = round(100 * statistics.mean(action_confidences), 1) if action_confidences else None
    execution_confidence = (
        round((execution_coverage / 100) * execution_evidence_quality, 1)
        if execution_coverage is not None and execution_evidence_quality is not None else None
    )

    opportunity = Counter()
    for finding in open_findings:
        opportunity[finding.get("severity", "unknown")] += 1
    opportunity_values: dict[str, float] = {}
    opportunity_confidences: dict[str, float] = {}
    opportunity_fact_ids: dict[str, str] = {}
    for fact in facts:
        key = fact.get("key")
        value = fact.get("value")
        if (
            key in OPPORTUNITY_WEIGHTS
            and fact.get("status") in RELIABLE_FACT_STATUSES
            and isinstance(value, (int, float)) and not isinstance(value, bool)
            and 0 <= value <= 100
        ):
            opportunity_values[key] = float(value)
            opportunity_confidences[key] = CONFIDENCE_FACTOR.get(fact.get("confidence"), 0.0)
            opportunity_fact_ids[key] = str(fact.get("fact_id"))
    opportunity_measured_weight = sum(OPPORTUNITY_WEIGHTS[key] for key in opportunity_values)
    opportunity_coverage = round(100 * opportunity_measured_weight / sum(OPPORTUNITY_WEIGHTS.values()), 1)
    opportunity_raw_score = (
        round(sum(opportunity_values[key] * OPPORTUNITY_WEIGHTS[key] for key in opportunity_values) / opportunity_measured_weight, 1)
        if opportunity_measured_weight else None
    )
    opportunity_score = opportunity_raw_score if opportunity_coverage >= 50 else None
    opportunity_confidence = (
        round(
            (opportunity_coverage / 100)
            * 100
            * sum(opportunity_confidences[key] * OPPORTUNITY_WEIGHTS[key] for key in opportunity_values)
            / opportunity_measured_weight,
            1,
        )
        if opportunity_measured_weight else None
    )

    limitations: list[str] = []
    if coverage_score is not None and coverage_score < 80:
        limitations.append("Couverture des contrôles inférieure à 80 %; ne pas présenter le score de fondation comme exhaustif.")
    if len(runs) < 3:
        limitations.append("Moins de trois runs GEO enregistrés; la volatilité reste sous-observée.")
    limitations.extend(geo.get("limitations", []))
    if opportunity_coverage < 50:
        limitations.append("Moins de 50 % des composantes d’opportunité sont documentées; aucun score O n’est publié.")

    geo_segments = geo.get("segments", [])
    usable_geo = sum(segment.get("metrics", {}).get("usable_observations", 0) for segment in geo_segments)
    attempted_geo = sum(segment.get("metrics", {}).get("attempted_observations", 0) for segment in geo_segments)
    return {
        "schema_version": "3.0", "generated_at": utc_now(),
        "as_of": as_of.astimezone(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "input_fingerprint": input_fingerprint(project), "audit_id": manifest.get("audit_id"),
        "principle": "Five independent F/V/O/E/M dimensions; no global score is computed.",
        "dimensions": {
            "F_foundations": {
                "dimension_code": "F", "name": "foundations",
                "score": foundation_score, "coverage_pct": foundation_coverage, "confidence_pct": foundation_confidence,
                "status": "available" if foundation_score is not None else "insufficient_data",
                "formula": "100 moins les pénalités de sévérité pondérées par la confiance; les poids sont renormalisés sur les catégories effectivement contrôlées.",
                "severity_penalties": SEVERITY_PENALTY, "confidence_factors": CONFIDENCE_FACTOR,
                "categories": category_scores,
            },
            "V_ai_visibility": {
                "dimension_code": "V", "name": "ai_visibility", "score": None,
                "status": "available" if usable_geo else "insufficient_data",
                "coverage_pct": geo.get("panel_coverage_pct"), "confidence_pct": None,
                "overall": geo.get("overall", {}), "segments": geo_segments,
                "stability": geo.get("stability", {}),
                "note": "Observed rates are reported per homogeneous context; no mixed-context rate or synthetic visibility score is inferred.",
            },
            "O_opportunity": {
                "dimension_code": "O", "name": "opportunity", "score": opportunity_score,
                "status": "available" if opportunity_score is not None else "insufficient_data",
                "coverage_pct": opportunity_coverage, "confidence_pct": opportunity_confidence,
                "components": {key: opportunity_values.get(key) for key in OPPORTUNITY_WEIGHTS},
                "weights": OPPORTUNITY_WEIGHTS,
                "fact_ids": opportunity_fact_ids,
                "inventory": {"open_findings_by_severity": dict(sorted(opportunity.items()))},
                "note": "Le score est publié seulement avec au moins 50 % de composantes business fiables; il n’est jamais inféré du nombre de constats.",
            },
            "E_execution": {
                "dimension_code": "E", "name": "execution", "score": execution_score,
                "status": "available" if execution_score is not None else "insufficient_data",
                "coverage_pct": execution_coverage, "confidence_pct": execution_confidence,
                "components": {"weighted_progress_pct": progress_score, "owned_actions_pct": ownership_score, "dated_actions_pct": due_date_score, "testable_actions_pct": acceptance_score},
                "weights": {"weighted_progress_pct": 50, "owned_actions_pct": 20, "dated_actions_pct": 15, "testable_actions_pct": 15},
                "active_actions": len(active_actions),
            },
            "M_measurement": {
                "dimension_code": "M", "name": "measurement", "score": measurement_score,
                "status": "available" if measurement_score is not None else "insufficient_data",
                "coverage_pct": measurement_coverage, "confidence_pct": measurement_confidence,
                "components": measurement_components, "weights": component_weights,
                "raw_score_before_coverage_gate": measurement_raw_score,
                "expected_checks": len(expected), "observed_expected_checks": len(expected & observed), "missing_checks": sorted(expected - observed),
            },
        },
        "limitations": list(dict.fromkeys(limitations)),
    }


def canonical_score_errors(
    project: Path,
    payload: Any,
    as_of: dt.datetime | None = None,
) -> list[str]:
    """Recalculate and verify the full deterministic score contract."""

    if not isinstance(payload, dict):
        return ["Le score canonique doit être un objet JSON."]
    generated_at = payload.get("generated_at")
    try:
        generated_datetime = parse_datetime(generated_at)
    except (TypeError, ValueError):
        return ["generated_at du score doit être une date ISO 8601 avec fuseau."]
    try:
        manifest_created_at = parse_datetime(read_json(project / "audit_manifest.json").get("created_at"))
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return ["created_at du manifeste est absent ou invalide."]
    if generated_datetime < manifest_created_at:
        return ["generated_at du score ne peut pas précéder la création de l’audit."]
    if generated_datetime > dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=5):
        return ["generated_at du score ne peut pas être situé dans le futur."]
    try:
        payload_as_of = parse_datetime(payload.get("as_of"))
    except (TypeError, ValueError):
        return ["as_of du score doit être une date ISO 8601 avec fuseau."]
    effective_as_of = as_of or payload_as_of
    if effective_as_of.tzinfo is None or effective_as_of.utcoffset() is None:
        return ["La date de coupure attendue doit inclure un fuseau."]
    expected_as_of = effective_as_of.astimezone(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    if payload.get("as_of") != expected_as_of:
        return [f"as_of du score ne correspond pas à la coupure attendue ({expected_as_of})."]
    try:
        expected = calculate_scores(project, effective_as_of)
    except Exception as exc:
        return [f"Recalcul du score impossible: {exc}."]
    candidate_comparable = {key: value for key, value in payload.items() if key != "generated_at"}
    expected_comparable = {key: value for key, value in expected.items() if key != "generated_at"}
    if candidate_comparable != expected_comparable:
        return [
            "Le contenu du score canonique diffère du recalcul déterministe courant "
            "(dimensions, formules, données ou structure altérées)."
        ]
    return []


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--as-of", help="Date-time ISO pour rendre le calcul de fraîcheur reproductible")
    parser.add_argument("--output", type=Path, help="Sortie JSON (défaut: PROJECT/reports/score_v3.json)")
    parser.add_argument("--stdout", action="store_true", help="Écrire le JSON sur stdout sans créer de fichier")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        as_of = parse_datetime(args.as_of) if args.as_of else None
    except (TypeError, ValueError) as exc:
        print(f"ERREUR: --as-of invalide: {exc}")
        return 2
    result = calculate_scores(args.project.resolve(), as_of)
    if args.stdout:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        output = (args.output or args.project.resolve() / "reports" / "score_v3.json").resolve()
        write_json(output, result)
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
