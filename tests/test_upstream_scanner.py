import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "tooling" / "upstream" / "scan.py"


def load_scanner():
    spec = importlib.util.spec_from_file_location("upstream_scanner", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class UpstreamScannerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scanner = load_scanner()

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        snapshot = self.root / "snapshot"
        snapshot.mkdir()
        (snapshot / "candidate.md").write_text("# Candidate\n", encoding="utf-8")
        self.registry = self.root / "sources.yaml"
        self.source = {
            "id": "fixture",
            "upstream_url": "https://example.invalid/repo",
            "ref": "abc123",
            "local_snapshot": "snapshot",
            "policy": "metadata-only-no-network-no-execution",
        }
        self._write_registry()

    def _write_registry(self) -> None:
        self.registry.write_text(
            json.dumps({"schema_version": 1, "sources": [self.source]}),
            encoding="utf-8",
        )

    def test_scan_is_deterministic_and_metadata_only(self):
        first = self.scanner.render_report(self.scanner.scan_sources(self.root, self.registry))
        second = self.scanner.render_report(self.scanner.scan_sources(self.root, self.registry))
        payload = json.loads(first)

        self.assertEqual(first, second)
        self.assertEqual(payload["mode"], "read-only")
        self.assertEqual(payload["sources"][0]["files"][0]["path"], "snapshot/candidate.md")

    def test_executable_registry_field_is_rejected(self):
        self.source["command"] = "curl https://example.invalid"
        self._write_registry()

        with self.assertRaisesRegex(self.scanner.UpstreamScanError, "executable field forbidden"):
            self.scanner.scan_sources(self.root, self.registry)


if __name__ == "__main__":
    unittest.main()
