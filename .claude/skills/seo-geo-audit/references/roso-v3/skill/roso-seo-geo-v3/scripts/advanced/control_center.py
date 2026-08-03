#!/usr/bin/env python3
"""Generate an offline, static multi-project RosoAI V3 control center."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from _advanced_common import load_geo_runs, load_optional_json, pct, project_dirs, read_json, utc_now, write_json, write_text


SCORE_CANDIDATES = (
    "score_v3.json", "reports/score_v3.json", "exports/score_v3.json",
    "scores_v3.json", "reports/scores_v3.json", "exports/scores_v3.json",
)


def _client_name(project: Path, manifest: dict[str, Any]) -> str:
    path = project / "client.yaml"
    if path.is_file():
        lines = path.read_text(encoding="utf-8").splitlines()
        in_identity = False
        for line in lines:
            stripped = line.strip()
            if not line.startswith(" ") and stripped.endswith(":"):
                in_identity = stripped == "identity:"
                continue
            if in_identity:
                match = re.match(r"\s+name:\s*(.+?)\s*$", line)
                if match:
                    return match.group(1).strip("'\"")
    return str(manifest.get("client_id") or project.name)


def _core_input_fingerprint(project: Path) -> str:
    scripts_dir = Path(__file__).resolve().parent.parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from score_v3 import input_fingerprint  # type: ignore

    return input_fingerprint(project)


def _valid_as_of(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _score(project: Path, audit_id: str) -> tuple[dict[str, Any] | None, str | None, list[str]]:
    for candidate in SCORE_CANDIDATES:
        path = project / candidate
        if path.is_file():
            score = read_json(path)
            if not isinstance(score, dict):
                return None, candidate, [f"{candidate}: objet score invalide; score exclu."]
            if score.get("audit_id") != audit_id:
                return None, candidate, [f"{candidate}: audit_id ne correspond pas au manifeste; score exclu."]
            fingerprint = score.get("input_fingerprint")
            if not isinstance(fingerprint, str) or fingerprint != _core_input_fingerprint(project):
                return None, candidate, [f"{candidate}: empreinte des entrées absente ou obsolète; score exclu."]
            if not _valid_as_of(score.get("as_of")):
                return None, candidate, [f"{candidate}: as_of absent ou sans fuseau; score exclu."]
            return score, candidate, []
    return None, None, []


def _evidence_issues(project: Path, audit_id: str) -> list[str]:
    path = project / "evidence.jsonl"
    if not path.is_file():
        return []
    issues: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [f"evidence.jsonl: lecture impossible ({exc}); données exclues."]
    for line_number, raw in enumerate(lines, 1):
        if not raw.strip():
            continue
        try:
            evidence = json.loads(raw)
        except json.JSONDecodeError as exc:
            issues.append(f"evidence.jsonl:{line_number}: JSON invalide ({exc.msg}); données exclues.")
            continue
        if not isinstance(evidence, dict):
            issues.append(f"evidence.jsonl:{line_number}: objet attendu; données exclues.")
            continue
        if evidence.get("audit_id") != audit_id:
            evidence_id = evidence.get("evidence_id", "unknown")
            issues.append(
                f"evidence.jsonl:{line_number} ({evidence_id}): audit_id ne correspond pas au manifeste; preuve exclue."
            )
    return issues


def _geo_summary(project: Path, audit_id: str) -> tuple[dict[str, Any], list[str]]:
    runs = load_geo_runs([project]) if (project / "geo_runs").is_dir() else []
    issues = [
        f"geo_runs/{run.get('run_id', 'unknown')}: audit_id ne correspond pas au manifeste; run exclu."
        for run in runs if run.get("audit_id") != audit_id
    ]
    runs = [run for run in runs if run.get("audit_id") == audit_id]
    observations = [item for run in runs for item in run.get("observations", [])]
    segmented: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for run in runs:
        session = run.get("session", {})
        for observation in run.get("observations", []):
            origin = observation.get("prompt_origin", {})
            key = (
                str(run.get("engine", "unknown")), str(run.get("model", "unknown")),
                str(run.get("surface", "unknown")), str(run.get("locale", "unknown")),
                str(run.get("country", "unknown")), str(run.get("device", "unknown")),
                str(run.get("account_state", "unknown")), str(run.get("personalization", "unknown")),
                str(run.get("web_access", "unknown")), str(run.get("panel_version", "unknown")),
                str(observation.get("query_type", "unknown")), str(observation.get("funnel_stage", "unknown")),
                str(observation.get("intent", "unknown")), str(session.get("context_state", "unknown")),
                str(session.get("client_material_exposure", "unknown")),
                str(session.get("documentation_status", "unknown")), str(origin.get("type", "unknown")),
                str(origin.get("reference", "unknown")), str(observation.get("persona", "unknown")),
                str(observation.get("criticality", "unknown")),
            )
            segmented.setdefault(key, []).append(observation)
    segments: list[dict[str, Any]] = []
    all_usable: list[dict[str, Any]] = []
    for key, items in sorted(segmented.items()):
        usable = [item for item in items if item.get("response_status") == "ok"]
        all_usable.extend(usable)
        mentioned = sum(item.get("brand_mentioned") is True for item in usable)
        cited = sum(any(citation.get("is_brand") for citation in item.get("citations", [])) for item in usable)
        segments.append({
            "context": dict(zip(
                (
                    "engine", "model", "surface", "locale", "country", "device", "account_state",
                    "personalization", "web_access", "panel_version", "query_type", "funnel_stage", "intent",
                    "session_context_state", "client_material_exposure", "session_documentation_status",
                    "prompt_origin", "prompt_origin_reference", "persona", "criticality",
                ),
                key,
            )),
            "attempted_observations": len(items), "usable_observations": len(usable),
            "mention_rate_pct": pct(mentioned, len(usable)), "cited_prompt_rate_pct": pct(cited, len(usable)),
        })
    claims = Counter(
        str(claim.get("status", "unverifiable"))
        for item in all_usable for claim in item.get("claims", [])
    )
    latest = max((str(item.get("captured_at")) for item in observations if item.get("captured_at")), default=None)
    return {
        "runs": len(runs), "observations": len(observations), "usable_observations": len(all_usable),
        "segments": segments,
        "claims": {key: claims[key] for key in ("accurate", "inaccurate", "outdated", "unverifiable")},
        "latest_capture": latest,
    }, issues


def _registry(project: Path, filename: str, collection: str, audit_id: str) -> tuple[list[dict[str, Any]], list[str]]:
    data = load_optional_json(project / filename, {})
    if not data:
        return [], []
    if not isinstance(data, dict) or data.get("audit_id") != audit_id:
        return [], [f"{filename}: audit_id ne correspond pas au manifeste; données exclues."]
    records = data.get(collection, [])
    if not isinstance(records, list):
        return [], [f"{filename}: collection {collection} invalide; données exclues."]
    return records, []


def project_summary(project: Path, include_path: bool = False) -> dict[str, Any]:
    manifest = read_json(project / "audit_manifest.json")
    audit_id = str(manifest.get("audit_id"))
    _, fact_issues = _registry(project, "facts.json", "facts", audit_id)
    findings, finding_issues = _registry(project, "findings.json", "findings", audit_id)
    actions, action_issues = _registry(project, "actions.json", "actions", audit_id)
    evidence_issues = _evidence_issues(project, audit_id)
    score, score_source, score_issues = _score(project, audit_id)
    geo, geo_issues = _geo_summary(project, audit_id)
    scoring_input_issues = evidence_issues + fact_issues + finding_issues + action_issues + geo_issues
    if score is not None and scoring_input_issues:
        score_issues.append(
            f"{score_source}: score non publiable car au moins une entrée structurée est rattachée à un autre audit."
        )
        score = None
    data_issues = scoring_input_issues + score_issues
    dimensions = (score or {}).get("dimensions", {})
    action_status = Counter(str(item.get("status", "unknown")) for item in actions)
    open_findings = [item for item in findings if item.get("status") in {"open", "accepted", "in_progress", "blocked"}]
    severity = Counter(str(item.get("severity", "unknown")) for item in open_findings)
    summary: dict[str, Any] = {
        "client_name": _client_name(project, manifest), "client_id": manifest.get("client_id"),
        "audit_id": manifest.get("audit_id"), "audit_status": manifest.get("status"),
        "root_url": manifest.get("scope", {}).get("root_url"), "vertical": manifest.get("scope", {}).get("vertical"),
        "markets": manifest.get("scope", {}).get("markets", []), "locales": manifest.get("scope", {}).get("locales", []),
        "updated_at": manifest.get("updated_at"), "open_findings": len(open_findings),
        "finding_severity": dict(severity), "actions_total": len(actions), "action_status": dict(action_status),
        "actions_done": action_status["done"], "actions_blocked": action_status["blocked"],
        "scores": {
            code: {
                "score": item.get("score"), "coverage_pct": item.get("coverage_pct"),
                "confidence_pct": item.get("confidence_pct"), "status": item.get("status"),
            }
            for code, item in dimensions.items()
        },
        "score_source": score_source, "score_publishable": score is not None,
        "score_as_of": score.get("as_of") if score else None,
        "score_input_fingerprint": score.get("input_fingerprint") if score else None,
        "geo": geo, "data_issues": data_issues,
        "blind_spots": manifest.get("blind_spots", []),
    }
    if include_path:
        summary["project_path"] = str(project)
    return summary


def build_control_center(projects: list[Path], include_paths: bool = False) -> dict[str, Any]:
    summaries = [project_summary(path, include_paths) for path in projects]
    return {
        "schema_version": "3.0", "generated_at": utc_now(), "project_count": len(summaries),
        "projects": summaries,
        "portfolio": {
            "open_findings": sum(item["open_findings"] for item in summaries),
            "actions_total": sum(item["actions_total"] for item in summaries),
            "actions_done": sum(item["actions_done"] for item in summaries),
            "actions_blocked": sum(item["actions_blocked"] for item in summaries),
            "geo_runs": sum(item["geo"]["runs"] for item in summaries),
            "narrative_alerts": sum(
                item["geo"]["claims"].get("inaccurate", 0) + item["geo"]["claims"].get("outdated", 0)
                for item in summaries
            ),
            "data_integrity_warnings": sum(len(item["data_issues"]) for item in summaries),
        },
        "limitations": [
            "Le dashboard reflète uniquement les fichiers locaux présents au moment de sa génération; il ne se met pas à jour seul.",
            "L'absence d'une mesure est affichée comme non disponible et ne vaut jamais zéro.",
            "Les scores restent séparés; aucune moyenne globale de portefeuille n'est calculée.",
        ],
    }


def _score_cell(project: dict[str, Any], code: str) -> str:
    item = project.get("scores", {}).get(code, {})
    if not item or item.get("status") != "available" or item.get("score") is None:
        return '<span class="muted">Non disponible</span>'
    try:
        score = max(0.0, min(100.0, float(item["score"])))
    except (TypeError, ValueError):
        return '<span class="muted">Valeur invalide</span>'
    details = []
    for label, key in (("Couverture", "coverage_pct"), ("Confiance", "confidence_pct")):
        value = item.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            details.append(f"{label} {float(value):g} %")
        elif value is not None:
            details.append(f"{label} invalide")
    disclosure = f"<small>{html.escape(' · '.join(details))}</small>" if details else ""
    return (
        f'<span class="score" aria-label="{score:g} sur 100"><span style="width:{score:g}%"></span></span>'
        f'<b>{score:g}</b>{disclosure}'
    )


def _segment_cell(geo: dict[str, Any], metric: str) -> str:
    segments = [item for item in geo.get("segments", []) if item.get(metric) is not None]
    if not segments:
        return '<span class="muted">Non mesuré</span>'
    values = [float(item[metric]) for item in segments]
    if len(segments) == 1:
        return f"{values[0]:g}%<small>{segments[0]['usable_observations']} obs. utilisables</small>"
    details = []
    for item in segments:
        context = item["context"]
        label = " / ".join(
            context[key]
            for key in (
                "engine", "model", "surface", "locale", "country", "device", "account_state",
                "personalization", "web_access", "panel_version", "query_type", "funnel_stage", "intent",
                "session_context_state", "client_material_exposure", "session_documentation_status",
                "prompt_origin", "persona", "criticality",
            )
        )
        details.append(f"<li>{html.escape(label)}: {float(item[metric]):g}% (n={item['usable_observations']})</li>")
    return (
        f"{min(values):g}–{max(values):g}%"
        f"<details><summary>{len(segments)} segments</summary><ul>{''.join(details)}</ul></details>"
    )


def render_html(data: dict[str, Any], title: str = "RosoAI SEO/GEO — Control Center") -> str:
    esc = lambda value: html.escape(str(value if value is not None else ""), quote=True)
    rows = []
    for item in data["projects"]:
        geo = item["geo"]
        narrative_alerts = geo["claims"].get("inaccurate", 0) + geo["claims"].get("outdated", 0)
        integrity = f"<small class=\"integrity\">Intégrité: {len(item['data_issues'])} alerte(s)</small>" if item["data_issues"] else ""
        rows.append(
            "<tr>"
            f"<th scope=\"row\"><span class=\"client\">{esc(item['client_name'])}</span><small>{esc(item['audit_id'])}</small>{integrity}</th>"
            f"<td><span class=\"status status-{esc(item['audit_status'])}\">{esc(item['audit_status'])}</span></td>"
            f"<td>{esc(item['vertical'])}<small>{esc(', '.join(item['markets']))}</small></td>"
            f"<td>{item['open_findings']}<small>P0/critique: {item['finding_severity'].get('critical', 0)}</small></td>"
            f"<td>{item['actions_done']}/{item['actions_total']}<small>Bloquées: {item['actions_blocked']}</small></td>"
            f"<td>{_score_cell(item, 'F_foundations')}</td>"
            f"<td>{_score_cell(item, 'E_execution')}</td>"
            f"<td>{_score_cell(item, 'M_measurement')}</td>"
            f"<td>{_segment_cell(geo, 'mention_rate_pct')}</td>"
            f"<td>{_segment_cell(geo, 'cited_prompt_rate_pct')}<small>{geo['runs']} run(s)</small></td>"
            f"<td>{narrative_alerts}<small>Non vérifiables: {geo['claims'].get('unverifiable', 0)}</small></td>"
            f"<td>{esc(item['updated_at'])}<small>Score: {esc(item['score_as_of'] or 'non publiable')}</small>"
            f"<small>GEO: {esc(geo['latest_capture'] or 'non mesuré')}</small></td>"
            "</tr>"
        )
    portfolio = data["portfolio"]
    limitations = "".join(f"<li>{esc(item)}</li>" for item in data["limitations"])
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:">
<title>{esc(title)}</title><style>
:root{{--ink:#15222c;--muted:#64717c;--line:#d9e1e6;--paper:#fff;--wash:#f4f7f8;--brand:#087f73;--warn:#a95f00}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--wash);color:var(--ink);font:14px/1.45 system-ui,-apple-system,sans-serif}}
main{{max-width:1500px;margin:auto;padding:32px}}header{{display:flex;justify-content:space-between;align-items:end;gap:24px;margin-bottom:24px}}
h1{{font-size:clamp(24px,4vw,40px);margin:0}}p{{margin:.25rem 0;color:var(--muted)}}.cards{{display:grid;grid-template-columns:repeat(6,minmax(130px,1fr));gap:12px;margin:20px 0}}
.card{{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:16px}}.card b{{display:block;font-size:26px}}.card span,small{{display:block;color:var(--muted);font-size:12px}}
.table-wrap{{overflow:auto;background:var(--paper);border:1px solid var(--line);border-radius:14px}}table{{border-collapse:collapse;width:100%;min-width:1250px}}
th,td{{padding:13px 12px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}}thead th{{position:sticky;top:0;background:#eaf1f1;font-size:12px;text-transform:uppercase;letter-spacing:.04em}}
.client{{font-weight:750;display:block}}.status{{display:inline-block;border:1px solid var(--line);border-radius:99px;padding:2px 8px;background:#fff}}.status-complete{{color:#096b42;border-color:#8bcab0}}.status-paused,.status-cancelled{{color:var(--warn)}}
.integrity{{color:#9a3f00}}details summary{{cursor:pointer;color:var(--brand)}}details ul{{min-width:230px}}
.score{{display:inline-block;width:70px;height:7px;margin:6px 7px 0 0;border-radius:8px;background:#dfe7e8;overflow:hidden;vertical-align:top}}.score span{{display:block;height:100%;background:var(--brand)}}.muted{{color:var(--muted)}}
section.notes{{margin-top:20px;padding:16px 20px;background:#fff;border:1px solid var(--line);border-radius:12px}}section.notes h2{{font-size:16px;margin:0 0 8px}}ul{{margin:.3rem 0;padding-left:20px}}
@media(max-width:900px){{main{{padding:18px}}header{{display:block}}.cards{{grid-template-columns:repeat(2,1fr)}}}}
@media print{{body{{background:#fff}}main{{max-width:none;padding:0}}.table-wrap{{overflow:visible}}}}
</style></head><body><main>
<header><div><h1>{esc(title)}</h1><p>Vue locale multi-projets — aucune synchronisation externe.</p></div><p>Généré le {esc(data['generated_at'])}</p></header>
<div class="cards" aria-label="Synthèse du portefeuille">
<div class="card"><b>{data['project_count']}</b><span>projets</span></div><div class="card"><b>{portfolio['open_findings']}</b><span>constats ouverts</span></div>
<div class="card"><b>{portfolio['actions_done']}/{portfolio['actions_total']}</b><span>actions terminées</span></div><div class="card"><b>{portfolio['actions_blocked']}</b><span>actions bloquées</span></div>
<div class="card"><b>{portfolio['geo_runs']}</b><span>runs GEO</span></div><div class="card"><b>{portfolio['narrative_alerts']}</b><span>alertes narratives · intégrité {portfolio['data_integrity_warnings']}</span></div></div>
<div class="table-wrap"><table><caption class="muted">État des audits, mesures et plans d'action</caption><thead><tr>
<th>Client / audit</th><th>Statut</th><th>Périmètre</th><th>Constats</th><th>Actions</th><th>F — Fondations</th><th>E — Exécution</th><th>M — Mesure</th><th>Mention IA</th><th>Citation IA</th><th>Récit</th><th>Actualisation</th>
</tr></thead><tbody>{''.join(rows) if rows else '<tr><td colspan="12">Aucun projet détecté.</td></tr>'}</tbody></table></div>
<section class="notes"><h2>Limites de lecture</h2><ul>{limitations}</ul></section>
</main></body></html>"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path, help="Projet(s) ou dossier contenant plusieurs projets")
    parser.add_argument("--output", type=Path, required=True, help="Dashboard HTML statique")
    parser.add_argument("--data-output", type=Path, help="Snapshot JSON optionnel")
    parser.add_argument("--title", default="RosoAI SEO/GEO — Control Center")
    parser.add_argument("--recursive", action="store_true", help="Chercher les projets récursivement")
    parser.add_argument("--include-paths", action="store_true", help="Inclure les chemins locaux dans le JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        projects = project_dirs(args.inputs, args.recursive)
        if not projects:
            raise ValueError("Aucun projet contenant audit_manifest.json n'a été trouvé.")
        data = build_control_center(projects, args.include_paths)
        write_text(args.output, render_html(data, args.title))
        if args.data_output:
            write_json(args.data_output, data)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"ERREUR: {exc}") from exc
    print(f"Dashboard généré: {args.output} ({len(projects)} projet(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
