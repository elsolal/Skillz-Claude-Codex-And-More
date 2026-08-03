#!/usr/bin/env python3
"""Regression tests for the standard-library advanced V3 scripts."""

from __future__ import annotations

import csv
import contextlib
import copy
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ADVANCED = Path(__file__).resolve().parents[1]
if str(ADVANCED) not in sys.path:
    sys.path.insert(0, str(ADVANCED))

import control_center  # noqa: E402
import delta_compare  # noqa: E402
import export_tickets  # noqa: E402
import import_metrics  # noqa: E402
import narrative_integrity  # noqa: E402
import rule_source_check  # noqa: E402
import source_graph  # noqa: E402


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )


def sample_run(run_id: str = "geo_test_001", repeat_index: int = 1) -> dict:
    return {
        "run_id": run_id, "audit_id": "audit_test_20260715", "engine": "chatgpt", "model": "test-model",
        "surface": "web-search", "locale": "fr-FR", "country": "FR", "device": "desktop",
        "account_state": "clean", "personalization": "off", "web_access": "on", "panel_version": "panel-v1",
        "session": {
            "context_state": "new", "client_material_exposure": "none", "documentation_status": "complete",
        },
        "planned_prompt_ids": ["prompt_test"],
        "repeat_index": repeat_index, "total_repeats": 2,
        "brand": {"name": "Example", "domain": "example.com", "aliases": ["Example Inc"]},
        "observations": [{
            "prompt_id": "prompt_test", "prompt_text": "Qui recommander ?", "intent": "commercial",
            "funnel_stage": "consideration", "query_type": "unbranded", "response_status": "ok",
            "prompt_origin": {"type": "search_observation", "reference": "fixture"},
            "persona": "acheteur_b2b", "criticality": "high", "brand_mentioned": True, "brand_position": 1,
            "recommendation_status": "positive",
            "citations": [{"url": "https://example.com/page", "domain": "example.com", "title": "Exemple", "is_brand": True}],
            "claims": [
                {"fact_key": "identity.name", "status": "accurate", "notes": "exact"},
                {"fact_key": "price.main", "status": "inaccurate", "notes": "prix faux"},
                {"fact_key": "person.ceo", "status": "outdated", "notes": "ancien dirigeant"},
                {"fact_key": "proof.award", "status": "unverifiable", "notes": "source absente"},
            ],
            "sentiment": "positive", "captured_at": "2026-07-15T10:00:00Z",
        }],
    }


def sample_manifest(locale: str = "fr-FR") -> dict:
    return {
        "audit_id": "audit_test_20260715", "client_id": "client_test", "status": "analyzing",
        "updated_at": "2026-07-15T10:00:00Z",
        "scope": {
            "root_url": "https://example.com/", "locales": [locale], "markets": ["France"],
            "vertical": "b2b", "mode": "full", "max_pages": 100,
            "include_urls": ["https://example.com/"], "exclude_patterns": ["/private/"],
            "expected_checks": ["crawl.http"],
        },
        "methodology": {"scoring_version": "3.0", "rules_snapshot_date": "2026-07-15"},
        "blind_spots": [],
    }


def sample_score(foundation: float, visibility_segments: list[dict] | None = None) -> dict:
    visibility_segments = visibility_segments or []
    return {
        "schema_version": "3.0", "generated_at": "2026-07-15T12:00:00Z",
        "as_of": "2026-07-15T12:00:00Z", "audit_id": "audit_test_20260715", "principle": "separate",
        "dimensions": {
            "F_foundations": {
                "name": "foundations", "status": "available", "score": foundation,
                "coverage_pct": 80.0, "confidence_pct": 75.0, "formula": "fixed",
                "categories": {"technical": {}},
            },
            "E_execution": {
                "name": "execution", "status": "available", "score": 50.0,
                "coverage_pct": 100.0, "confidence_pct": 85.0,
            },
            "M_measurement": {
                "name": "measurement", "status": "available", "score": 80.0,
                "coverage_pct": 90.0, "confidence_pct": 80.0, "weights": {"coverage": 100},
            },
            "V_ai_visibility": {
                "name": "ai_visibility", "status": "available" if visibility_segments else "insufficient_data",
                "score": None, "coverage_pct": 100.0 if visibility_segments else None,
                "confidence_pct": None,
                "overall": {
                    "status": "available_homogeneous_context" if len(visibility_segments) == 1 else (
                        "not_reported_mixed_contexts" if visibility_segments else "no_data"
                    ),
                    "context_count": len(visibility_segments),
                    "context": visibility_segments[0]["context"] if len(visibility_segments) == 1 else None,
                    "metrics": visibility_segments[0]["metrics"] if len(visibility_segments) == 1 else None,
                },
                "segments": visibility_segments,
                "stability": {},
            },
        },
    }


def write_scoring_inputs(
    project: Path,
    *,
    evidence_audit_id: str = "audit_test_20260715",
    runs: list[dict] | None = None,
) -> None:
    write_json(project / "audit_manifest.json", sample_manifest())
    write_json(project / "facts.json", {"audit_id": "audit_test_20260715", "facts": []})
    write_json(project / "findings.json", {"audit_id": "audit_test_20260715", "findings": []})
    write_json(project / "actions.json", {"audit_id": "audit_test_20260715", "actions": []})
    write_jsonl(project / "evidence.jsonl", [{
        "evidence_id": "ev_test", "audit_id": evidence_audit_id, "status": "observed",
        "confidence": "confirmed", "check_id": "crawl.http",
    }])
    (project / "geo_runs").mkdir(parents=True, exist_ok=True)
    for index, run in enumerate(runs or [], 1):
        write_json(project / "geo_runs" / f"run-{index}.json", run)


def write_linked_score(project: Path, score: dict, filename: str = "reports/score_v3.json") -> dict:
    core_scripts = ADVANCED.parent
    if str(core_scripts) not in sys.path:
        sys.path.insert(0, str(core_scripts))
    from score_v3 import input_fingerprint  # type: ignore

    linked = copy.deepcopy(score)
    linked["input_fingerprint"] = input_fingerprint(project)
    write_json(project / filename, linked)
    return linked


def visibility_segment(context: dict[str, str], mention_rate: float) -> dict:
    return {
        "context": context,
        "metrics": {
            "panel_coverage_pct": 100.0,
            "response_success_rate_pct": 100.0,
            "brand_mention_rate_pct": mention_rate,
            "brand_cited_prompt_rate_pct": mention_rate,
            "brand_citation_share_pct": mention_rate,
            "average_brand_position": 1.0,
            "narrative_accuracy_pct": 100.0,
            "positive_recommendation_rate_pct": mention_rate,
        },
    }


class AdvancedFeaturesTests(unittest.TestCase):
    def test_narrative_integrity_aggregates_all_statuses(self) -> None:
        report = narrative_integrity.aggregate_claims([sample_run()])
        self.assertEqual(report["overall"]["claims_total"], 4)
        self.assertEqual(report["overall"]["by_status"]["outdated"], 1)
        self.assertEqual(report["overall"]["accuracy_pct_excluding_unverifiable"], 33.3)
        self.assertIn("price.main", report["flagged_fact_keys"])

    def test_source_graph_emits_prompt_domain_url_and_csv(self) -> None:
        run = sample_run()
        run["observations"][0]["prompt_text"] = "=DANGEROUS()"
        run["observations"][0]["citations"][0]["title"] = "+DANGEROUS"
        graph = source_graph.build_graph([run])
        self.assertEqual(graph["citation_occurrences"], 1)
        self.assertEqual({node["type"] for node in graph["nodes"]}, {"prompt", "domain", "url"})
        self.assertEqual({edge["type"] for edge in graph["edges"]}, {"prompt_cites_domain", "domain_contains_url"})
        rows = list(csv.DictReader(io.StringIO(source_graph.paths_csv(graph))))
        self.assertEqual(rows[0]["domain"], "example.com")
        self.assertTrue(rows[0]["prompt_text"].startswith("'="))
        self.assertTrue(rows[0]["title"].startswith("'+"))

    def test_narrative_csv_blocks_formula_injection(self) -> None:
        run = sample_run()
        run["observations"][0]["claims"][0]["notes"] = "@DANGEROUS"
        report = narrative_integrity.aggregate_claims([run])
        rows = list(csv.DictReader(io.StringIO(narrative_integrity.details_csv(report))))
        self.assertTrue(rows[0]["notes"].startswith("'@"))

    def test_delta_compare_only_emits_compatible_delta(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            left, right = root / "left", root / "right"
            for project, score in ((left, sample_score(60.0)), (right, sample_score(75.0))):
                write_json(project / "audit_manifest.json", sample_manifest())
                write_json(project / "scores_v3.json", score)
                (project / "geo_runs").mkdir(parents=True)
            result = delta_compare.compare_snapshots(delta_compare.load_snapshot(left), delta_compare.load_snapshot(right))
            self.assertTrue(result["dimensions"]["F_foundations"]["comparable"])
            self.assertEqual(result["dimensions"]["F_foundations"]["score_delta"], 15.0)

            changed = sample_manifest("en-GB")
            write_json(right / "audit_manifest.json", changed)
            result = delta_compare.compare_snapshots(delta_compare.load_snapshot(left), delta_compare.load_snapshot(right))
            self.assertFalse(result["dimensions"]["F_foundations"]["comparable"])
            self.assertIsNone(result["dimensions"]["F_foundations"]["score_delta"])

    def test_delta_scope_checks_full_perimeter_and_ignores_list_order(self) -> None:
        base_manifest = sample_manifest()
        base_manifest["scope"]["locales"] = ["fr-FR", "en-GB"]
        base_manifest["scope"]["markets"] = ["France", "Belgique"]
        base_manifest["scope"]["include_urls"] = ["https://example.com/a", "https://example.com/b"]
        base_manifest["scope"]["exclude_patterns"] = ["/private/", "/cart/"]
        base_manifest["scope"]["expected_checks"] = ["crawl.http", "geo.panel"]

        reordered = copy.deepcopy(base_manifest)
        for key in ("locales", "markets", "include_urls", "exclude_patterns", "expected_checks"):
            reordered["scope"][key].reverse()
        blocking, _ = delta_compare._scope_reasons(base_manifest, reordered)
        self.assertEqual(blocking, [])

        changes = {
            "mode": "express",
            "root_url": "https://example.com:444/a",
            "include_urls": ["https://example.com/c"],
            "exclude_patterns": ["/different/"],
            "max_pages": 10,
            "expected_checks": ["other.check"],
        }
        for key, value in changes.items():
            with self.subTest(key=key):
                changed = copy.deepcopy(base_manifest)
                changed["scope"][key] = value
                blocking, _ = delta_compare._scope_reasons(base_manifest, changed)
                self.assertTrue(blocking)

    def test_delta_as_of_requires_timezone(self) -> None:
        with self.assertRaises(ValueError):
            delta_compare._parse_as_of("2026-07-15T12:00:00")
        self.assertIsNotNone(delta_compare._parse_as_of("2026-07-15T12:00:00Z"))

    def test_geo_signature_tracks_brand_repeats_and_multiplicity(self) -> None:
        first = sample_run("geo_test_001", 1)
        second = sample_run("geo_test_002", 2)
        baseline = delta_compare._geo_signature([first])
        complete = delta_compare._geo_signature([first, second])
        self.assertNotEqual(baseline, complete)

        duplicate = copy.deepcopy(first)
        duplicate["observations"].append(copy.deepcopy(duplicate["observations"][0]))
        self.assertNotEqual(baseline, delta_compare._geo_signature([duplicate]))

        rebranded = copy.deepcopy(first)
        rebranded["brand"]["name"] = "Different Brand"
        self.assertNotEqual(baseline, delta_compare._geo_signature([rebranded]))

    def test_delta_visibility_pairs_real_segments_independent_of_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            left, right = root / "left", root / "right"
            run = sample_run()
            second_observation = copy.deepcopy(run["observations"][0])
            second_observation.update({
                "prompt_id": "prompt_decision", "prompt_text": "Quelle solution choisir ?",
                "intent": "transactional", "funnel_stage": "decision", "persona": "direction_marketing",
                "criticality": "medium",
            })
            run["planned_prompt_ids"] = ["prompt_test", "prompt_decision"]
            run["observations"].append(second_observation)
            for project in (left, right):
                write_scoring_inputs(project, runs=[copy.deepcopy(run)])

            awareness_context = delta_compare._segment_context(run, run["observations"][0])
            decision_context = delta_compare._segment_context(run, run["observations"][1])
            baseline_segments = [
                visibility_segment(awareness_context, 20.0),
                visibility_segment(decision_context, 30.0),
            ]
            current_segments = [
                visibility_segment(decision_context, 50.0),
                visibility_segment(awareness_context, 40.0),
            ]
            write_linked_score(left, sample_score(70.0, baseline_segments))
            write_linked_score(right, sample_score(70.0, current_segments))

            result = delta_compare.compare_snapshots(
                delta_compare.load_snapshot(left), delta_compare.load_snapshot(right),
            )
            visibility = result["dimensions"]["V_ai_visibility"]
            self.assertTrue(visibility["comparable"], visibility)
            self.assertEqual(visibility["metric_deltas"], {})
            by_funnel = {
                item["context"]["funnel_stage"]: item for item in visibility["segment_deltas"]
            }
            self.assertEqual(by_funnel["consideration"]["metric_deltas"]["brand_mention_rate_pct"]["delta"], 20.0)
            self.assertEqual(by_funnel["decision"]["metric_deltas"]["brand_mention_rate_pct"]["delta"], 20.0)

    def test_delta_visibility_neutralizes_changed_context_or_signature(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            left, right = root / "left", root / "right"
            baseline_run = sample_run()
            second_observation = copy.deepcopy(baseline_run["observations"][0])
            second_observation.update({
                "prompt_id": "prompt_decision", "prompt_text": "Quelle solution choisir ?",
                "intent": "transactional", "funnel_stage": "decision", "persona": "direction_marketing",
            })
            baseline_run["planned_prompt_ids"] = ["prompt_test", "prompt_decision"]
            baseline_run["observations"].append(second_observation)
            changed_run = copy.deepcopy(baseline_run)
            changed_run["observations"][1]["funnel_stage"] = "retention"
            write_scoring_inputs(left, runs=[baseline_run])
            write_scoring_inputs(right, runs=[changed_run])

            baseline_segments = [
                visibility_segment(delta_compare._segment_context(baseline_run, observation), rate)
                for observation, rate in zip(baseline_run["observations"], (20.0, 30.0))
            ]
            current_segments = [
                visibility_segment(delta_compare._segment_context(changed_run, observation), rate)
                for observation, rate in zip(changed_run["observations"], (40.0, 50.0))
            ]
            write_linked_score(left, sample_score(70.0, baseline_segments))
            write_linked_score(right, sample_score(70.0, current_segments))
            changed = delta_compare.compare_snapshots(
                delta_compare.load_snapshot(left), delta_compare.load_snapshot(right),
            )["dimensions"]["V_ai_visibility"]
            self.assertFalse(changed["comparable"])
            by_funnel = {item["context"]["funnel_stage"]: item for item in changed["segment_deltas"]}
            self.assertTrue(by_funnel["consideration"]["comparable"])
            self.assertFalse(by_funnel["decision"]["comparable"])
            self.assertFalse(by_funnel["retention"]["comparable"])
            self.assertIsNone(by_funnel["decision"]["metric_deltas"]["brand_mention_rate_pct"]["delta"])

            signature_changed_run = copy.deepcopy(baseline_run)
            signature_changed_run["observations"][1]["prompt_text"] = "Texte de prompt modifié"
            write_json(right / "geo_runs" / "run-1.json", signature_changed_run)
            same_context_segments = [
                visibility_segment(delta_compare._segment_context(baseline_run, observation), rate)
                for observation, rate in zip(baseline_run["observations"], (40.0, 50.0))
            ]
            write_linked_score(right, sample_score(70.0, same_context_segments))
            signature_changed = delta_compare.compare_snapshots(
                delta_compare.load_snapshot(left), delta_compare.load_snapshot(right),
            )["dimensions"]["V_ai_visibility"]
            self.assertFalse(signature_changed["comparable"])
            signature_by_funnel = {
                item["context"]["funnel_stage"]: item for item in signature_changed["segment_deltas"]
            }
            self.assertTrue(signature_by_funnel["consideration"]["comparable"])
            self.assertFalse(signature_by_funnel["decision"]["comparable"])
            self.assertTrue(any("prompts" in reason for reason in signature_by_funnel["decision"]["reasons"]))

    def test_ticket_export_blocks_csv_formula_injection(self) -> None:
        action = {
            "action_id": "action_test", "title": "=HYPERLINK(\"bad\")", "description": "+cmd", "stream": "build",
            "priority": "P1", "status": "ready", "effort": {"size": "S", "person_days": 1}, "impact": "high",
            "owner": "@owner", "due_date": "2026-08-01", "finding_ids": ["finding_test"], "evidence_ids": [],
            "dependencies": [], "acceptance_criteria": ["Test validé"], "validation_method": "Recrawler",
            "rollback": "Restaurer", "target_urls": [], "risk": "low", "approval_required": True, "automation": "assisted",
        }
        rows = list(csv.DictReader(io.StringIO(export_tickets.render_csv([action], "generic"))))
        self.assertTrue(rows[0]["title"].startswith("'="))
        self.assertTrue(rows[0]["owner"].startswith("'@"))

    def test_import_metrics_normalizes_local_csv(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "gsc.csv"
            path.write_text("Date;Requête;Clics;Impressions;CTR;Position\n2026-07-01;seo geo;12;100;12,5%;3,2\n", encoding="utf-8")
            records = import_metrics.normalize_csv(path, "gsc", "audit_test_20260715", "2026-07-15T12:00:00Z")
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["source_type"], "search_console")
            self.assertEqual(records[0]["authorization_permission"], "read_gsc")
            self.assertEqual(records[0]["metadata"]["metrics"]["ctr_pct"], 12.5)
            self.assertEqual(records[0]["metadata"]["dimensions"]["query"], "seo geo")
            expected_raw_hash = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(records[0]["raw_hash"], expected_raw_hash)
            self.assertEqual(records[0]["metadata"]["source_file_hash"], expected_raw_hash)

    def test_import_metrics_is_idempotent_and_duplicate_rows_get_unique_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            manifest = sample_manifest()
            manifest["authorization"] = {"permissions": ["read_gsc"]}
            write_json(project / "audit_manifest.json", manifest)
            (project / "evidence.jsonl").write_text("", encoding="utf-8")
            csv_path = root / "gsc.csv"
            csv_path.write_text("Date,Query,Clicks\n2026-07-01,seo geo,12\n2026-07-01,seo geo,12\n", encoding="utf-8")

            first = import_metrics.normalize_csv(csv_path, "gsc", "audit_test_20260715", "2026-07-15T12:00:00Z")
            self.assertEqual(len({item["evidence_id"] for item in first}), 2)
            self.assertEqual(len({item["raw_hash"] for item in first}), 1)

            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(import_metrics.main([
                    str(csv_path), "--source", "gsc", "--project", str(project), "--append",
                    "--collected-at", "2026-07-15T12:00:00Z",
                ]), 0)
                self.assertEqual(import_metrics.main([
                    str(csv_path), "--source", "gsc", "--project", str(project), "--append",
                    "--collected-at", "2026-07-16T12:00:00Z",
                ]), 0)
            records = [json.loads(line) for line in (project / "evidence.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(records), 2)
            self.assertEqual(len({item["evidence_id"] for item in records}), 2)

    def test_import_metrics_canonicalizes_ledger_path_before_overwrite_guard(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            (project / "sub").mkdir(parents=True)
            manifest = sample_manifest()
            manifest["authorization"] = {"permissions": ["read_gsc"]}
            write_json(project / "audit_manifest.json", manifest)
            ledger = project / "evidence.jsonl"
            original = '{"evidence_id":"ev_existing"}\n'
            ledger.write_text(original, encoding="utf-8")
            csv_path = root / "gsc.csv"
            csv_path.write_text("Date,Clicks\n2026-07-01,1\n", encoding="utf-8")
            disguised_ledger = project / "sub" / ".." / "evidence.jsonl"
            with contextlib.redirect_stderr(io.StringIO()):
                code = import_metrics.main([
                    str(csv_path), "--source", "gsc", "--project", str(project),
                    "--output", str(disguised_ledger),
                ])
            self.assertEqual(code, 2)
            self.assertEqual(ledger.read_text(encoding="utf-8"), original)

    def test_rule_source_check_is_offline_by_default(self) -> None:
        with mock.patch.object(rule_source_check, "_fetch", side_effect=AssertionError("network called")):
            report = rule_source_check.check_sources(["https://developers.google.com/search/updates"], network=False)
        self.assertFalse(report["network_requested"])
        self.assertEqual(report["results"][0]["check_status"], "not_checked")
        self.assertIsNone(report["results"][0]["content_sha256"])

    def test_rule_url_collection_rejects_non_allowlisted_domain(self) -> None:
        with self.assertRaises(ValueError):
            rule_source_check.collect_urls([], ["https://example.com/rules"], set(rule_source_check.DEFAULT_ALLOWED_DOMAINS))

    def test_control_center_escapes_client_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            write_json(project / "audit_manifest.json", sample_manifest())
            write_json(project / "findings.json", {"findings": []})
            write_json(project / "actions.json", {"actions": []})
            write_json(project / "scores_v3.json", sample_score(70.0))
            (project / "geo_runs").mkdir(parents=True)
            (project / "client.yaml").write_text("identity:\n  name: <script>alert(1)</script>\n", encoding="utf-8")
            data = control_center.build_control_center([project])
            rendered = control_center.render_html(data)
            self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", rendered)
            self.assertNotIn("<script>alert(1)</script>", rendered)
            self.assertIn("Content-Security-Policy", rendered)

    def test_control_center_separates_geo_contexts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            write_json(project / "audit_manifest.json", sample_manifest())
            write_json(project / "findings.json", {"audit_id": "audit_test_20260715", "findings": []})
            write_json(project / "actions.json", {"audit_id": "audit_test_20260715", "actions": []})
            write_json(project / "scores_v3.json", sample_score(70.0))
            first = sample_run("geo_test_001", 1)
            second = sample_run("geo_test_002", 2)
            second["engine"] = "perplexity"
            second["observations"][0]["query_type"] = "branded"
            write_json(project / "geo_runs" / "one.json", first)
            write_json(project / "geo_runs" / "two.json", second)
            data = control_center.build_control_center([project])
            geo = data["projects"][0]["geo"]
            self.assertEqual(len(geo["segments"]), 2)
            self.assertNotIn("mention_rate_pct", geo)
            contexts = {(item["context"]["engine"], item["context"]["query_type"]) for item in geo["segments"]}
            self.assertEqual(contexts, {("chatgpt", "unbranded"), ("perplexity", "branded")})
            self.assertIn("2 segments", control_center.render_html(data))

    def test_control_center_reads_canonical_score_and_keeps_funnel_segments(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            first = sample_run("geo_test_001", 1)
            second = sample_run("geo_test_002", 2)
            second["observations"][0]["funnel_stage"] = "decision"
            second["observations"][0]["intent"] = "transactional"
            write_scoring_inputs(project, runs=[first, second])
            linked = write_linked_score(project, sample_score(72.0))
            summary = control_center.project_summary(project)
            self.assertEqual(summary["score_source"], "reports/score_v3.json")
            self.assertTrue(summary["score_publishable"])
            self.assertEqual(summary["score_as_of"], "2026-07-15T12:00:00Z")
            self.assertEqual(summary["score_input_fingerprint"], linked["input_fingerprint"])
            self.assertEqual(summary["scores"]["F_foundations"]["score"], 72.0)
            self.assertEqual(summary["scores"]["F_foundations"]["coverage_pct"], 80.0)
            self.assertEqual(summary["scores"]["F_foundations"]["confidence_pct"], 75.0)
            self.assertEqual(len(summary["geo"]["segments"]), 2)
            rendered = control_center.render_html(control_center.build_control_center([project]))
            self.assertIn("test-model / web-search / fr-FR / FR / desktop", rendered)
            self.assertIn("decision / transactional", rendered)
            self.assertIn("Couverture 80 %", rendered)
            self.assertIn("Confiance 75 %", rendered)
            self.assertIn("Score: 2026-07-15T12:00:00Z", rendered)

    def test_alien_evidence_blocks_delta_and_control_center_score(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            left, right = root / "left", root / "right"
            write_scoring_inputs(left)
            write_scoring_inputs(right, evidence_audit_id="audit_alien")
            write_json(right / "facts.json", {"audit_id": "audit_alien", "facts": []})
            write_linked_score(left, sample_score(60.0))
            write_linked_score(right, sample_score(75.0))

            right_snapshot = delta_compare.load_snapshot(right)
            self.assertTrue(any("evidence.jsonl" in issue for issue in right_snapshot["linkage_issues"]))
            self.assertTrue(any("facts.json" in issue for issue in right_snapshot["linkage_issues"]))
            result = delta_compare.compare_snapshots(delta_compare.load_snapshot(left), right_snapshot)
            self.assertFalse(result["scope"]["compatible"])
            self.assertIsNone(result["dimensions"]["F_foundations"]["score_delta"])

            summary = control_center.project_summary(right)
            self.assertFalse(summary["score_publishable"])
            self.assertEqual(summary["scores"], {})
            self.assertTrue(any("evidence.jsonl" in issue for issue in summary["data_issues"]))
            self.assertTrue(any("facts.json" in issue for issue in summary["data_issues"]))
            self.assertTrue(any("non publiable" in issue for issue in summary["data_issues"]))

    def test_control_center_excludes_stale_score_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            write_scoring_inputs(project)
            write_linked_score(project, sample_score(72.0))
            actions = json.loads((project / "actions.json").read_text(encoding="utf-8"))
            actions["actions"].append({"action_id": "action_new", "status": "backlog"})
            write_json(project / "actions.json", actions)

            summary = control_center.project_summary(project)
            self.assertFalse(summary["score_publishable"])
            self.assertEqual(summary["scores"], {})
            self.assertTrue(any("empreinte" in issue and "score exclu" in issue for issue in summary["data_issues"]))

    def test_artifact_audit_ids_are_excluded_and_block_delta(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            left, right = root / "left", root / "right"
            for project in (left, right):
                write_json(project / "audit_manifest.json", sample_manifest())
                write_json(project / "scores_v3.json", sample_score(70.0))
                write_json(project / "findings.json", {"audit_id": "audit_test_20260715", "findings": []})
                write_json(project / "actions.json", {"audit_id": "audit_test_20260715", "actions": []})
                (project / "geo_runs").mkdir(parents=True)
            write_json(right / "actions.json", {"audit_id": "audit_other", "actions": [{"status": "done"}]})
            write_json(right / "findings.json", {"audit_id": "audit_other", "findings": [{"status": "open"}]})
            wrong_score = sample_score(70.0)
            wrong_score["audit_id"] = "audit_other"
            write_json(right / "scores_v3.json", wrong_score)
            wrong_run = sample_run()
            wrong_run["audit_id"] = "audit_other"
            write_json(right / "geo_runs" / "wrong.json", wrong_run)

            summary = control_center.project_summary(right)
            self.assertEqual(summary["actions_total"], 0)
            self.assertEqual(summary["open_findings"], 0)
            self.assertEqual(summary["scores"], {})
            self.assertEqual(summary["geo"]["runs"], 0)
            self.assertGreaterEqual(len(summary["data_issues"]), 4)

            result = delta_compare.compare_snapshots(delta_compare.load_snapshot(left), delta_compare.load_snapshot(right))
            self.assertFalse(result["scope"]["compatible"])
            self.assertTrue(any("audit_id" in reason for reason in result["scope"]["blocking_reasons"]))
            self.assertIsNone(result["dimensions"]["F_foundations"]["score_delta"])


if __name__ == "__main__":
    unittest.main()
