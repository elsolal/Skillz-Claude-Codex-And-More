import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "gate_verify.py"


def load_gate_module():
    spec = importlib.util.spec_from_file_location("gate_verify", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class GateVerifyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gate = load_gate_module()

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.email", "tests@example.invalid"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "Gate Tests"], cwd=self.root, check=True)
        (self.root / ".agents").mkdir()
        (self.root / ".agents" / "verification.yaml").write_text(
            'config_fingerprint: "fixture-fingerprint"\n'
            "commands:\n"
            '  lint: "bash scripts/lint.sh"\n'
            '  test: "python -m unittest"\n'
            "testability:\n"
            "  e2e: none\n",
            encoding="utf-8",
        )
        (self.root / "app.txt").write_text("base\n", encoding="utf-8")
        self._commit("base")
        self.base_sha = self._sha()
        (self.root / "app.txt").write_text("feature\n", encoding="utf-8")
        self._commit("feature")
        self.head_sha = self._sha()

    def _commit(self, message: str) -> None:
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", message], cwd=self.root, check=True)

    def _sha(self) -> str:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.root, text=True).strip()

    def _write_gate(
        self,
        *,
        invented: bool = False,
        missing_head: bool = False,
        verdict: str = "PASS",
        waiver: dict | None = None,
    ) -> Path:
        proof_path = self.root / "docs" / "quality" / "proofs" / "fixture.json"
        gate_path = self.root / "docs" / "quality" / "GATE-fixture.yaml"
        proof_path.parent.mkdir(parents=True)
        executions = [
            {"name": "lint", "command": "bash scripts/lint.sh", "status": "passed", "exit_code": 0},
            {"name": "test", "command": "python -m unittest", "status": "passed", "exit_code": 0},
        ]
        if invented:
            executions.append(
                {"name": "deploy", "command": "deploy production", "status": "passed", "exit_code": 0}
            )
        proof = {
            "schema_version": 1,
            "manifest_fingerprint": "fixture-fingerprint",
            "executions": executions,
            "absents": [],
        }
        if waiver is not None:
            proof["waiver"] = waiver
        proof_path.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        fields = [
            "schema_version: 2",
            f'verdict: "{verdict}"',
            'level: 3',
            f'base_sha: "{self.base_sha}"',
        ]
        if not missing_head:
            fields.append(f'head_sha: "{self.head_sha}"')
        fields.extend(
            [
                f'code_diff_hash: "{self.gate.compute_code_diff_hash(self.root, self.base_sha, self.head_sha, ["CHANGELOG.md"])}"',
                'code_diff_exclusions: ["CHANGELOG.md"]',
                'proof_payload: "docs/quality/proofs/fixture.json"',
                f'proof_payload_hash: "{hashlib.sha256(proof_path.read_bytes()).hexdigest()}"',
                f'integrity_sha256: "{"0" * 64}"',
            ]
        )
        gate_path.parent.mkdir(parents=True, exist_ok=True)
        gate_path.write_text("\n".join(fields) + "\n", encoding="utf-8")
        self.gate.seal_gate(gate_path)
        self._commit("quality evidence")
        return gate_path

    def _write_legacy_gate(self, *, matching_hash: bool = True) -> Path:
        gate_path = self.root / "docs" / "quality" / "GATE-legacy.yaml"
        gate_path.parent.mkdir(parents=True)
        diff_hash = self.gate.compute_legacy_diff_hash(self.root, self.base_sha, "HEAD")
        if not matching_hash:
            diff_hash = "0" * 64
        gate_path.write_text(
            "verdict: PASS\n"
            "niveau: 2\n"
            "tours: 2\n"
            f'diff_hash: "{diff_hash}"\n'
            "preuve:\n"
            "  executable:\n"
            "    test: { cmd: \"python -m unittest\", statut: vert }\n"
            "decisions_prises_en_ton_nom: []\n"
            "absents: []\n",
            encoding="utf-8",
        )
        self._commit("legacy quality evidence")
        return gate_path

    def test_fresh_gate_verifies(self):
        gate_path = self._write_gate()

        result = self.gate.verify_gate(self.root, gate_path)

        self.assertEqual(result["status"], "valid")

    def test_code_commit_after_gate_is_stale(self):
        gate_path = self._write_gate()
        (self.root / "app.txt").write_text("changed after gate\n", encoding="utf-8")
        self._commit("post-gate code")

        with self.assertRaisesRegex(self.gate.GateVerificationError, "non-evidence changes"):
            self.gate.verify_gate(self.root, gate_path)

    def test_modified_payload_invalidates_gate(self):
        gate_path = self._write_gate()
        proof_path = self.root / "docs" / "quality" / "proofs" / "fixture.json"
        proof_path.write_text(proof_path.read_text(encoding="utf-8") + " ", encoding="utf-8")

        with self.assertRaisesRegex(self.gate.GateVerificationError, "proof payload hash"):
            self.gate.verify_gate(self.root, gate_path)

    def test_missing_head_sha_is_rejected(self):
        gate_path = self._write_gate(missing_head=True)

        with self.assertRaisesRegex(self.gate.GateVerificationError, "head_sha"):
            self.gate.verify_gate(self.root, gate_path)

    def test_invented_command_is_rejected(self):
        gate_path = self._write_gate(invented=True)

        with self.assertRaisesRegex(self.gate.GateVerificationError, "invented or missing commands"):
            self.gate.verify_gate(self.root, gate_path)

    def test_manual_gate_edit_invalidates_integrity(self):
        gate_path = self._write_gate()
        gate_path.write_text(
            gate_path.read_text(encoding="utf-8").replace('verdict: "PASS"', 'verdict: "FAIL"'),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(self.gate.GateVerificationError, "integrity"):
            self.gate.verify_gate(self.root, gate_path)

    def test_resealed_but_uncommitted_gate_is_rejected(self):
        gate_path = self._write_gate()
        gate_path.write_text(
            gate_path.read_text(encoding="utf-8").replace("level: 3", "level: 2"),
            encoding="utf-8",
        )
        self.gate.seal_gate(gate_path)

        with self.assertRaisesRegex(self.gate.GateVerificationError, "uncommitted evidence"):
            self.gate.verify_gate(self.root, gate_path)

    def test_duplicate_top_level_field_is_rejected_even_when_resealed(self):
        gate_path = self._write_gate()
        gate_path.write_text(
            gate_path.read_text(encoding="utf-8") + 'verdict: "PASS"\n',
            encoding="utf-8",
        )
        self.gate.seal_gate(gate_path)

        with self.assertRaisesRegex(self.gate.GateVerificationError, "duplicate gate fields"):
            self.gate.verify_gate(self.root, gate_path)

    def test_legacy_gate_is_classified_without_being_called_stale(self):
        gate_path = self._write_legacy_gate()

        with self.assertRaisesRegex(self.gate.GateVerificationError, "legacy evidence"):
            self.gate.verify_gate(self.root, gate_path)

        result = self.gate.verify_gate(
            self.root,
            gate_path,
            allow_legacy=True,
            legacy_base_ref=self.base_sha,
        )

        self.assertEqual(result["status"], "legacy-valid")
        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(result["verdict"], "PASS")

    def test_legacy_gate_with_mismatched_diff_is_rejected(self):
        gate_path = self._write_legacy_gate(matching_hash=False)

        with self.assertRaisesRegex(self.gate.GateVerificationError, "legacy gate diff hash mismatch"):
            self.gate.verify_gate(
                self.root,
                gate_path,
                allow_legacy=True,
                legacy_base_ref=self.base_sha,
            )

    def test_legacy_hash_matches_the_v1_shell_contract(self):
        expected = hashlib.sha256(
            subprocess.check_output(
                [
                    "git",
                    "diff",
                    f"{self.base_sha}...HEAD",
                    "--",
                    ":(exclude)docs/quality",
                    ":(exclude)CHANGELOG.md",
                ],
                cwd=self.root,
            )
        ).hexdigest()

        self.assertEqual(
            self.gate.compute_legacy_diff_hash(self.root, self.base_sha),
            expected,
        )

    def test_legacy_gate_rejects_duplicate_identity_fields(self):
        gate_path = self._write_legacy_gate()
        gate_path.write_text(
            gate_path.read_text(encoding="utf-8") + "verdict: PASS\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(self.gate.GateVerificationError, "exactly one verdict"):
            self.gate.verify_gate(
                self.root,
                gate_path,
                allow_legacy=True,
                legacy_base_ref=self.base_sha,
            )

    def test_waived_gate_requires_explicit_metadata(self):
        gate_path = self._write_gate(verdict="WAIVED")

        with self.assertRaisesRegex(self.gate.GateVerificationError, "waiver metadata"):
            self.gate.verify_gate(self.root, gate_path)

    def test_waived_gate_requires_timezone_aware_approval(self):
        gate_path = self._write_gate(
            verdict="WAIVED",
            waiver={
                "reason": "Bounded release risk accepted",
                "scope": "fixture gate only",
                "approved_by": "human",
                "approved_at": "2026-09-02T10:00:00",
            },
        )

        with self.assertRaisesRegex(self.gate.GateVerificationError, "timezone"):
            self.gate.verify_gate(self.root, gate_path)

    def test_waived_gate_with_explicit_metadata_verifies(self):
        gate_path = self._write_gate(
            verdict="WAIVED",
            waiver={
                "reason": "Bounded release risk accepted",
                "scope": "fixture gate only",
                "approved_by": "human",
                "approved_at": "2026-09-02T10:00:00+01:00",
            },
        )

        result = self.gate.verify_gate(self.root, gate_path)

        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["verdict"], "WAIVED")


if __name__ == "__main__":
    unittest.main()
