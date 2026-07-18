from __future__ import annotations

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "manifest-v1"
sys.path.insert(0, str(SKILL_ROOT))

from memory_cli.contracts import RetrievalMode  # noqa: E402
from memory_cli.manifest import (  # noqa: E402
    ManifestError,
    discover_manifest,
    initial_route,
    load_manifest,
)


class ManifestDiscoveryTests(unittest.TestCase):
    def test_discovers_nearest_manifest_without_leaving_git_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir) / "repo"
            nested = repo / "packages" / "plugin"
            work_dir = nested / "src" / "feature"
            (repo / ".git").mkdir(parents=True)
            (nested / ".agents").mkdir(parents=True)
            work_dir.mkdir(parents=True)
            manifest_path = nested / ".agents" / "memory.yaml"
            manifest_path.write_text((FIXTURES / "valid.json").read_text())

            self.assertEqual(discover_manifest(work_dir), manifest_path.resolve())

    def test_discovery_does_not_use_manifest_above_git_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            repo = parent / "repo"
            work_dir = repo / "src"
            (parent / ".agents").mkdir()
            (parent / ".agents" / "memory.yaml").write_text("{}")
            (repo / ".git").mkdir(parents=True)
            work_dir.mkdir()

            with self.assertRaisesRegex(ManifestError, "inside Git root"):
                discover_manifest(work_dir)


class ManifestContractTests(unittest.TestCase):
    def load_payload(self) -> dict[str, object]:
        return json.loads((FIXTURES / "valid.json").read_text())

    def write_payload(self, root: Path, payload: object) -> Path:
        (root / ".git").mkdir()
        (root / ".agents").mkdir()
        path = root / ".agents" / "memory.yaml"
        path.write_text(json.dumps(payload))
        return path

    def test_valid_manifest_exposes_typed_contract_and_route(self) -> None:
        manifest = load_manifest(FIXTURES / "valid.json")

        self.assertEqual(manifest.project.id, "skillz-claude")
        self.assertEqual(manifest.stores.project.collection, "elsolal-wiki")
        self.assertEqual(manifest.budgets[RetrievalMode.PROJECT].hard_tokens, 4000)
        self.assertEqual(manifest.policy.retention_days, 30)
        self.assertEqual(manifest.golden.visible_path.as_posix(), ".agents/memory/golden.json")
        self.assertIsNone(manifest.golden.start_question)
        self.assertEqual(
            initial_route(manifest, role="owner", task_category="architecture"),
            ("elsolal-wiki", "shared-wiki"),
        )
        self.assertEqual(
            initial_route(manifest, role="collaborator", task_category="architecture"),
            ("elsolal-wiki",),
        )

    def test_rejects_absolute_traversal_invalid_id_and_forbidden_key(self) -> None:
        cases = (
            (("stores", "project", "entry_pages"), ["/private/wiki.md"], "relative path"),
            (("stores", "project", "entry_pages"), ["wiki/../secret.md"], "traversal"),
            (("project", "id"), "Skillz_Claude", "lowercase kebab-case"),
            (("policy", "command"), "curl example.test", "unknown key"),
        )

        for field_path, invalid_value, expected in cases:
            with self.subTest(field_path=field_path):
                payload = self.load_payload()
                target = payload
                for key in field_path[:-1]:
                    target = target[key]  # type: ignore[index,assignment]
                target[field_path[-1]] = invalid_value  # type: ignore[index]
                with tempfile.TemporaryDirectory() as temp_dir:
                    path = self.write_payload(Path(temp_dir), payload)
                    with self.assertRaises(ManifestError) as raised:
                        load_manifest(path)
                self.assertEqual(raised.exception.exit_code, 30)
                self.assertIn(expected, raised.exception.correction)
                self.assertIn(".".join(field_path), raised.exception.field)

    def test_rejects_remote_credentials_and_url_entry_pages(self) -> None:
        cases = (
            (("stores", "project", "remote"), "https://token@example.test/memory.git", "without credentials"),
            (("stores", "project", "entry_pages"), ["https://example.test/wiki.md"], "not a URL"),
        )
        for field_path, invalid_value, expected in cases:
            with self.subTest(field_path=field_path):
                payload = self.load_payload()
                target = payload
                for key in field_path[:-1]:
                    target = target[key]  # type: ignore[index,assignment]
                target[field_path[-1]] = invalid_value  # type: ignore[index]
                with tempfile.TemporaryDirectory() as temp_dir:
                    path = self.write_payload(Path(temp_dir), payload)
                    with self.assertRaises(ManifestError) as raised:
                        load_manifest(path)
                self.assertIn(expected, raised.exception.correction)

    def test_accepts_optional_start_question_and_rejects_multiline_content(self) -> None:
        payload = self.load_payload()
        payload["golden"]["start_question"] = "What should I know before this task?"  # type: ignore[index]
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest = load_manifest(self.write_payload(Path(temp_dir), payload))
        self.assertEqual(manifest.golden.start_question, "What should I know before this task?")

        payload["golden"]["start_question"] = "line one\nline two"  # type: ignore[index]
        with tempfile.TemporaryDirectory() as temp_dir:
            path = self.write_payload(Path(temp_dir), payload)
            with self.assertRaises(ManifestError) as raised:
                load_manifest(path)
        self.assertEqual(raised.exception.code, "invalid_start_question")

    def test_rejects_free_yaml_with_v1_constraint(self) -> None:
        with self.assertRaises(ManifestError) as raised:
            load_manifest(FIXTURES / "free-yaml.yaml")

        self.assertEqual(raised.exception.code, "manifest_not_json_compatible")
        self.assertIn("JSON-compatible YAML", raised.exception.correction)

    def test_rejects_duplicate_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "memory.yaml"
            path.write_text('{"schema_version": 1, "schema_version": 1}')
            with self.assertRaises(ManifestError) as raised:
                load_manifest(path)

        self.assertEqual(raised.exception.code, "duplicate_key")

    def test_rejects_non_standard_json_constants(self) -> None:
        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(constant=constant), tempfile.TemporaryDirectory() as temp_dir:
                path = Path(temp_dir) / "memory.yaml"
                path.write_text(f'{{"schema_version": 1, "value": {constant}}}')
                with self.assertRaises(ManifestError) as raised:
                    load_manifest(path)

            self.assertEqual(raised.exception.code, "invalid_json_constant")
            self.assertIn("finite JSON number", raised.exception.correction)

    def test_unreadable_manifest_error_does_not_expose_its_absolute_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            unreadable_manifest = Path(temp_dir) / "private-memory.yaml"
            unreadable_manifest.mkdir()

            with self.assertRaises(ManifestError) as raised:
                load_manifest(unreadable_manifest)

        self.assertEqual(raised.exception.code, "manifest_unreadable")
        self.assertEqual(raised.exception.field, ".agents/memory.yaml")
        self.assertNotIn(str(unreadable_manifest), raised.exception.message)

    def test_unknown_schema_version_stops_before_route_decision(self) -> None:
        payload = self.load_payload()
        payload["schema_version"] = 99
        with tempfile.TemporaryDirectory() as temp_dir:
            path = self.write_payload(Path(temp_dir), payload)
            with self.assertRaises(ManifestError) as raised:
                load_manifest(path)

        self.assertEqual(raised.exception.code, "unsupported_schema_version")
        self.assertEqual(raised.exception.field, "schema_version")

    def test_parse_and_route_p95_stays_under_300_ms(self) -> None:
        durations_ms: list[float] = []
        for _ in range(40):
            started = time.perf_counter()
            manifest = load_manifest(FIXTURES / "valid.json")
            initial_route(manifest, role="owner", task_category="architecture")
            durations_ms.append((time.perf_counter() - started) * 1000)

        p95_index = max(0, int(len(durations_ms) * 0.95) - 1)
        p95_ms = sorted(durations_ms)[p95_index]
        self.assertLess(p95_ms, 300, f"manifest parse + route p95 was {p95_ms:.2f} ms")


if __name__ == "__main__":
    unittest.main()
