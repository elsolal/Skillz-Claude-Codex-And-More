from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "manifest-v1" / "valid.json"
EXPECTED = SKILL_ROOT / "expected_outputs" / "memory"


class ManifestCliContractTests(unittest.TestCase):
    def run_cli(self, cwd: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(SKILL_ROOT)
        return subprocess.run(
            [sys.executable, "-m", "memory_cli", "manifest", *arguments],
            cwd=cwd,
            env=environment,
            check=False,
            text=True,
            capture_output=True,
        )

    def make_repo(self, payload: str) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temp_dir = tempfile.TemporaryDirectory()
        repo = Path(temp_dir.name) / "repo"
        work_dir = repo / "src" / "nested"
        (repo / ".git").mkdir(parents=True)
        (repo / ".agents").mkdir()
        (repo / ".agents" / "memory.yaml").write_text(payload)
        work_dir.mkdir(parents=True)
        return temp_dir, work_dir

    def test_json_success_uses_stable_public_envelope(self) -> None:
        temp_dir, work_dir = self.make_repo(FIXTURE.read_text())
        self.addCleanup(temp_dir.cleanup)

        result = self.run_cli(work_dir, "--json")
        output = json.loads(result.stdout)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            list(output),
            ["schema_version", "command", "status", "project_id", "event_id", "data", "warnings", "errors"],
        )
        self.assertEqual(output["command"], "manifest")
        self.assertEqual(output["project_id"], "skillz-claude")
        self.assertEqual(output["data"]["manifest_schema_version"], 1)
        self.assertEqual(output["errors"], [])
        self.assertEqual(output, json.loads((EXPECTED / "manifest-valid.json").read_text()))

    def test_invalid_manifest_returns_exit_30_and_copyable_correction(self) -> None:
        payload = json.loads(FIXTURE.read_text())
        payload["schema_version"] = 99
        temp_dir, work_dir = self.make_repo(json.dumps(payload))
        self.addCleanup(temp_dir.cleanup)

        result = self.run_cli(work_dir, "--json")
        output = json.loads(result.stdout)

        self.assertEqual(result.returncode, 30)
        self.assertEqual(output["schema_version"], 1)
        self.assertEqual(output["status"], "blocked")
        self.assertIsNone(output["project_id"])
        self.assertEqual(output["data"], {})
        self.assertEqual(output["errors"][0]["field"], "schema_version")
        self.assertIn('Set "schema_version" to 1', output["errors"][0]["correction"])
        self.assertEqual(output, json.loads((EXPECTED / "manifest-invalid-version.json").read_text()))

    def test_human_error_names_field_and_correction(self) -> None:
        payload = json.loads(FIXTURE.read_text())
        payload["project"]["id"] = "INVALID_ID"
        temp_dir, work_dir = self.make_repo(json.dumps(payload))
        self.addCleanup(temp_dir.cleanup)

        result = self.run_cli(work_dir)

        self.assertEqual(result.returncode, 30)
        self.assertIn("project.id", result.stdout)
        self.assertIn("Correction:", result.stdout)
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
