#!/usr/bin/env python3
"""Generate two evidence-bound Markdown reports from a validated V3 project."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from collections import Counter
from pathlib import Path
from typing import Any

from _common import load_simple_yaml, parse_datetime, read_json, read_jsonl, utc_now, write_json, write_text
from score_v3 import calculate_scores, input_fingerprint


SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}


def md(value: Any) -> str:
    if value is None:
        return "Non mesuré"
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def score_label(value: Any) -> str:
    return "Non mesuré" if value is None else f"{value}/100"


def score_with_coverage(dimension: dict[str, Any]) -> str:
    score = score_label(dimension.get("score"))
    coverage = dimension.get("coverage_pct")
    confidence = dimension.get("confidence_pct")
    details = []
    if coverage is not None:
        details.append(f"couverture {coverage} %")
    if confidence is not None:
        details.append(f"confiance {confidence} %")
    return score if not details else f"{score} — {' — '.join(details)}"


def resolve_scores(
    project: Path,
    score_path: Path | None = None,
    as_of: dt.datetime | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    """Reuse the canonical score only when inputs and requested cutoff match."""
    canonical = (score_path or project / "reports" / "score_v3.json").resolve()
    fingerprint = input_fingerprint(project)
    expected_as_of = (
        as_of.astimezone(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        if as_of else None
    )
    if canonical.is_file():
        candidate = read_json(canonical)
        if (
            isinstance(candidate, dict)
            and candidate.get("audit_id") == read_json(project / "audit_manifest.json").get("audit_id")
            and candidate.get("input_fingerprint") == fingerprint
            and (expected_as_of is None or candidate.get("as_of") == expected_as_of)
        ):
            return candidate
    result = calculate_scores(project, as_of)
    if persist:
        write_json(canonical, result)
    return result


def generate_reports(
    project: Path,
    output_dir: Path | None = None,
    score_path: Path | None = None,
    as_of: dt.datetime | None = None,
) -> tuple[Path, Path]:
    project = project.resolve()
    output_dir = (output_dir or project / "reports").resolve()
    client = load_simple_yaml(project / "client.yaml")
    manifest = read_json(project / "audit_manifest.json")
    evidence = read_jsonl(project / "evidence.jsonl")
    findings = read_json(project / "findings.json").get("findings", [])
    actions = read_json(project / "actions.json").get("actions", [])
    scores = resolve_scores(project, score_path, as_of)
    identity = client.get("identity", {})
    client_name = identity.get("name", manifest.get("client_id"))
    is_fictional_demo = str(identity.get("domain", "")).lower().endswith(".example")
    title_suffix = " — EXEMPLE FICTIF" if is_fictional_demo else ""
    demo_notice = (
        "> **EXEMPLE FICTIF.** Les domaines, observations, métriques et recommandations de ce dossier servent uniquement à démontrer la méthode V3."
        if is_fictional_demo else None
    )
    generated = utc_now()

    severity_counts = Counter(finding.get("severity", "unknown") for finding in findings if finding.get("status") not in {"resolved", "dismissed"})
    v_coverage = scores["dimensions"]["V_ai_visibility"].get("coverage_pct")
    v_coverage_label = "couverture non mesurée" if v_coverage is None else f"couverture {v_coverage} %"
    audit: list[str] = [
        f"# Audit stratégique SEO/GEO — {md(client_name)}{title_suffix}",
        "",
        f"- Audit : `{md(manifest.get('audit_id'))}`",
        f"- Périmètre : {md(manifest.get('scope', {}).get('root_url'))}",
        f"- Marché / langue : {md(', '.join(manifest.get('scope', {}).get('markets', [])))} / {md(', '.join(manifest.get('scope', {}).get('locales', [])))}",
        f"- Généré : {generated}",
        f"- Version de méthode : {md(manifest.get('methodology', {}).get('kit_version'))}",
        "",
        *([demo_notice, ""] if demo_notice else []),
        "> Ce rapport est généré uniquement depuis les données structurées du projet. Un élément non observé est indiqué comme non mesuré; aucune promesse de classement, citation ou chiffre d'affaires n'est formulée.",
        "",
        "## Synthèse",
        "",
        f"L'audit contient **{len(findings)} constats**, **{len(evidence)} preuves** et **{len(actions)} actions**. "
        f"Les constats ouverts se répartissent ainsi : {', '.join(f'{key} : {value}' for key, value in sorted(severity_counts.items(), key=lambda item: SEVERITY_ORDER.get(item[0], 99))) or 'aucun'}.",
        "",
        "## Indicateurs séparés",
        "",
        "| Dimension | Résultat | Interprétation |",
        "|---|---:|---|",
        f"| F — Fondations | {score_with_coverage(scores['dimensions']['F_foundations'])} | Risque observé dans les catégories effectivement contrôlées |",
        f"| V — Visibilité IA | Mesures séparées — {v_coverage_label} | Mentions, citations, exactitude et stabilité observées |",
        f"| O — Opportunité | {score_with_coverage(scores['dimensions']['O_opportunity'])} | Demande, valeur, écart de contenu et faisabilité documentés |",
        f"| E — Exécution | {score_with_coverage(scores['dimensions']['E_execution'])} | Progression et caractère testable du plan |",
        f"| M — Mesure | {score_with_coverage(scores['dimensions']['M_measurement'])} | Couverture, confiance, fraîcheur et répétitions GEO |",
        "",
        "Ces dimensions ne sont pas moyennées dans une note globale.",
        "",
        "### Visibilité IA observée",
        "",
        "Les taux restent segmentés par contexte homogène. Aucun taux global n'est calculé lorsque moteur, modèle, surface, locale, marché, appareil, panel, type de requête, funnel ou intention diffèrent.",
        "",
        "| Contexte | N exploitable | Mention | Prompts citant la marque | Part des citations | Exactitude narrative |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    geo_segments = scores["dimensions"]["V_ai_visibility"].get("segments", [])
    for segment in geo_segments:
        context = segment.get("context", {})
        metrics = segment.get("metrics", {})
        context_label = " · ".join(
            md(context.get(key))
            for key in ("engine", "model", "surface", "locale", "country", "query_type", "funnel_stage", "intent")
        )
        def rate(key: str) -> str:
            value = metrics.get(key)
            return "Non mesuré" if value is None else f"{value} %"
        audit.append(
            f"| {context_label} | {md(metrics.get('usable_observations'))} | "
            f"{rate('brand_mention_rate_pct')} | {rate('brand_cited_prompt_rate_pct')} | "
            f"{rate('brand_citation_share_pct')} | {rate('narrative_accuracy_pct')} |"
        )
    if not geo_segments:
        audit.append("| Aucun segment mesuré | 0 | Non mesuré | Non mesuré | Non mesuré | Non mesuré |")
    audit.extend([
        "",
        "### Protocole du panel et recommandation",
        "",
        "| Contexte | Couverture panel | Recommandation positive | Persona | Origine | Criticité |",
        "|---|---:|---:|---|---|---|",
    ])
    for segment in geo_segments:
        context = segment.get("context", {})
        metrics = segment.get("metrics", {})
        context_label = " · ".join(
            md(context.get(key))
            for key in ("engine", "surface", "locale", "query_type", "funnel_stage", "intent")
        )
        def protocol_rate(key: str) -> str:
            value = metrics.get(key)
            return "Non mesuré" if value is None else f"{value} %"
        audit.append(
            f"| {context_label} | {protocol_rate('panel_coverage_pct')} | "
            f"{protocol_rate('positive_recommendation_rate_pct')} | {md(context.get('persona'))} | "
            f"{md(context.get('prompt_origin_type'))} | {md(context.get('criticality'))} |"
        )
    if not geo_segments:
        audit.append("| Aucun segment mesuré | Non mesuré | Non mesuré | Non mesuré | Non mesuré | Non mesuré |")
    audit.extend(["", "## Constats documentés", ""])

    ordered_findings = sorted(findings, key=lambda item: (SEVERITY_ORDER.get(item.get("severity"), 99), item.get("finding_id", "")))
    if not ordered_findings:
        audit.extend(["Aucun constat n'est enregistré. Cela ne signifie pas que le site est exempt de problème : vérifier la couverture de mesure.", ""])
    for finding in ordered_findings:
        audit.extend([
            f"### [{md(finding.get('severity')).upper()}] {md(finding.get('title'))}",
            "",
            f"- ID : `{md(finding.get('finding_id'))}`",
            "",
            f"**Constat.** {md(finding.get('statement'))}",
            "",
            f"**Impact.** {md(finding.get('impact'))}",
            "",
            f"**Dimension / base / confiance.** {md(finding.get('dimension'))} / {md(finding.get('basis'))} / {md(finding.get('confidence'))}",
            "",
            f"**Preuves.** {', '.join(f'`{md(ref)}`' for ref in finding.get('evidence_ids', []))}",
        ])
        urls = finding.get("affected_urls", [])
        if urls:
            audit.extend(["", f"**URLs concernées.** {', '.join(md(url) for url in urls)}"])
        for limitation in finding.get("limitations", []):
            audit.extend(["", f"- Limite : {md(limitation)}"])
        audit.append("")

    audit.extend(["## Registre synthétique des preuves", "", "| ID | Source | Statut | Confiance | Date |", "|---|---|---|---|---|"])
    for record in evidence:
        source = record.get("url") or record.get("source_label") or record.get("source_type")
        audit.append(f"| `{md(record.get('evidence_id'))}` | {md(source)} | {md(record.get('status'))} | {md(record.get('confidence'))} | {md(record.get('collected_at'))} |")
    audit.extend(["", "## Angles morts et limites", ""])
    limitations = list(manifest.get("blind_spots", [])) + list(scores.get("limitations", []))
    if limitations:
        audit.extend(f"- {md(item)}" for item in dict.fromkeys(limitations))
    else:
        audit.append("- Aucun angle mort n'a été documenté; ce point doit être revu avant livraison.")
    audit.extend([
        "", "## Méthode", "",
        f"Snapshot de règles : {md(manifest.get('methodology', {}).get('rules_snapshot_date'))}. "
        f"Scores arrêtés au : {md(scores.get('as_of'))}. "
        f"Formule de fondation : {md(scores['dimensions']['F_foundations']['formula'])}",
        "",
    ])

    plan: list[str] = [
        f"# Plan d'implémentation SEO/GEO — {md(client_name)}{title_suffix}",
        "",
        f"- Audit source : `{md(manifest.get('audit_id'))}`",
        f"- Généré : {generated}",
        "",
        *([demo_notice, ""] if demo_notice else []),
        "> Toute écriture externe, publication ou modification de CMS reste soumise aux permissions du manifeste et à une validation humaine lorsque celle-ci est requise.",
        "",
        "## Vue d'ensemble",
        "",
        "| Priorité | Backlog | Prête | En cours | Revue | Terminée | Bloquée |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for priority in ("P0", "P1", "P2", "P3"):
        statuses = Counter(action.get("status") for action in actions if action.get("priority") == priority)
        plan.append(f"| {priority} | {statuses['backlog']} | {statuses['ready']} | {statuses['in_progress']} | {statuses['in_review']} | {statuses['done']} | {statuses['blocked']} |")
    plan.extend(["", "## Actions", ""])
    ordered_actions = sorted(actions, key=lambda item: (PRIORITY_ORDER.get(item.get("priority"), 99), item.get("action_id", "")))
    if not ordered_actions:
        plan.extend(["Aucune action enregistrée.", ""])
    for action in ordered_actions:
        effort = action.get("effort", {})
        plan.extend([
            f"### {md(action.get('priority'))} — {md(action.get('title'))}",
            "",
            f"- ID : `{md(action.get('action_id'))}`",
            f"- Flux / statut : {md(action.get('stream'))} / {md(action.get('status'))}",
            f"- Propriétaire : {md(action.get('owner'))}",
            f"- Effort : {md(effort.get('size'))} ({md(effort.get('person_days'))} jour(s)-personne)",
            f"- Impact attendu : {md(action.get('impact'))}",
            f"- Confiance : {md(action.get('confidence'))}",
            f"- Échéance : {md(action.get('due_date'))}",
            f"- Approbation requise : {'oui' if action.get('approval_required') else 'non'}",
            "",
            md(action.get("description")),
            "",
            f"**Constats sources.** {', '.join(f'`{md(ref)}`' for ref in action.get('finding_ids', []))}",
            "",
            "**Critères d'acceptation**",
            "",
        ])
        plan.extend(f"- {md(item)}" for item in action.get("acceptance_criteria", []))
        plan.extend([
            "",
            f"**Validation.** {md(action.get('validation_method'))}",
            "",
            f"**Rollback.** {md(action.get('rollback'))}",
            "",
            f"**Dépendances.** {', '.join(f'`{md(ref)}`' for ref in action.get('dependencies', [])) or 'Aucune'}",
            "",
        ])
    plan.extend([
        "## Gouvernance de publication",
        "",
        f"- Permissions accordées : {', '.join(md(item) for item in manifest.get('authorization', {}).get('permissions', []))}",
        f"- Validation des écritures : {'obligatoire' if manifest.get('authorization', {}).get('write_actions_require_approval') else 'selon action'}",
        f"- Conservation : {md(manifest.get('data_policy', {}).get('retention_days'))} jours",
        f"- Politique PII : {md(manifest.get('data_policy', {}).get('pii'))}",
        f"- Secrets : {md(manifest.get('data_policy', {}).get('secrets'))}",
        "",
    ])

    audit_path = output_dir / "audit_strategique.md"
    plan_path = output_dir / "plan_implementation.md"
    write_text(audit_path, "\n".join(audit))
    write_text(plan_path, "\n".join(plan))
    return audit_path, plan_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--scores", type=Path, help="Fichier score_v3.json canonique à réutiliser s’il correspond aux entrées")
    parser.add_argument("--as-of", help="Date-time ISO avec fuseau pour un recalcul reproductible")
    parser.add_argument("--dry-run", action="store_true", help="Prévisualiser sans écrire de rapport")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        as_of = parse_datetime(args.as_of) if args.as_of else None
    except (TypeError, ValueError) as exc:
        print(json.dumps({"error": f"--as-of invalide: {exc}"}, ensure_ascii=False, indent=2))
        return 2
    if args.dry_run:
        project = args.project.resolve()
        output_dir = (args.output_dir or project / "reports").resolve()
        manifest = read_json(project / "audit_manifest.json")
        findings = read_json(project / "findings.json").get("findings", [])
        actions = read_json(project / "actions.json").get("actions", [])
        evidence = read_jsonl(project / "evidence.jsonl")
        scores = resolve_scores(project, args.scores, as_of, persist=False)
        print(json.dumps({
            "dry_run": True,
            "files_written": 0,
            "audit_id": manifest.get("audit_id"),
            "would_write": [
                str(output_dir / "audit_strategique.md"),
                str(output_dir / "plan_implementation.md"),
            ],
            "counts": {
                "evidence": len(evidence),
                "findings": len(findings),
                "actions": len(actions),
            },
            "dimension_statuses": {
                code: value.get("status") for code, value in scores.get("dimensions", {}).items()
            },
        }, ensure_ascii=False, indent=2))
        return 0
    paths = generate_reports(args.project, args.output_dir, args.scores, as_of)
    print("\n".join(str(path) for path in paths))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
