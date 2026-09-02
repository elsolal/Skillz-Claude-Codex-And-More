import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "tooling" / "testing" / "behavioral_harness.py"


def load_harness():
    spec = importlib.util.spec_from_file_location("behavioral_harness", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BehavioralHarnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.harness = load_harness()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.fixture = self.root / "fixture"
        self.fixture.mkdir()
        (self.fixture / "unchanged.txt").write_text("stable\n", encoding="utf-8")

    def passing_case(self) -> dict:
        script = (
            "from pathlib import Path; "
            "Path('created.txt').write_text('verdict=PASS\\n'); "
            "print('EVENT:probe\\nEVENT:plan\\nPlan ready')"
        )
        return {
            "id": "fixture-pass",
            "runtime": "fixture",
            "skill": "workflow.dev",
            "fixture": str(self.fixture),
            "input": "fix it",
            "repeat": 1,
            "timeout_seconds": 10,
            "permissions": "workspace_fixture_only",
            "runner": {"type": "command", "command": [sys.executable, "-c", script]},
            "expect": {
                "events_in_order": ["probe", "plan"],
                "files_exist": ["created.txt"],
                "files_absent": ["forbidden.txt"],
                "files_unchanged": ["unchanged.txt"],
                "file_contains": {"created.txt": ["verdict=PASS"]},
                "file_matches": {"created.txt": ["PASS$"]},
                "stdout_contains": ["Plan ready"],
            },
        }

    def test_runner_evaluates_generic_assertions_and_hashes(self):
        result = self.harness.run_case(
            self.passing_case(),
            repo_root=REPO_ROOT,
            base_sha="a" * 40,
            head_sha="b" * 40,
            iteration=1,
        )

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["events"], ["probe", "plan"])
        self.assertEqual(result["base_sha"], "a" * 40)
        self.assertNotEqual(result["hashes_before"], result["hashes_after"])
        self.assertTrue(all(item["passed"] for item in result["assertions"]))

    def test_failure_is_preserved_with_actionable_assertion(self):
        case = self.passing_case()
        case["expect"]["files_exist"] = ["missing.txt"]
        failures = self.root / "failures"

        result = self.harness.run_case(
            case,
            repo_root=REPO_ROOT,
            base_sha="a" * 40,
            head_sha="b" * 40,
            iteration=1,
            failure_root=failures,
        )

        self.assertEqual(result["status"], "failed")
        self.assertTrue(any(not item["passed"] for item in result["assertions"]))
        self.assertTrue(Path(result["preserved_workspace"]).is_dir())

    def test_dangerous_permission_bypass_is_rejected(self):
        case = self.passing_case()
        case["runner"]["command"].append("--dangerously-skip-permissions")

        with self.assertRaisesRegex(self.harness.HarnessError, "permission bypass"):
            self.harness.run_case(
                case,
                repo_root=REPO_ROOT,
                base_sha="a" * 40,
                head_sha="b" * 40,
                iteration=1,
            )

    def test_assertion_path_cannot_escape_workspace(self):
        case = self.passing_case()
        case["expect"]["files_exist"] = ["../outside.txt"]

        with self.assertRaisesRegex(self.harness.HarnessError, "unsafe assertion path"):
            self.harness.run_case(
                case,
                repo_root=REPO_ROOT,
                base_sha="a" * 40,
                head_sha="b" * 40,
                iteration=1,
            )

    def test_fixture_symlink_is_rejected(self):
        (self.fixture / "escape").symlink_to(self.root / "outside")

        with self.assertRaisesRegex(self.harness.HarnessError, "fixture contains a symlink"):
            self.harness.run_case(
                self.passing_case(),
                repo_root=REPO_ROOT,
                base_sha="a" * 40,
                head_sha="b" * 40,
                iteration=1,
            )

    def test_suite_supports_repeat_jobs_and_run_result_envelope(self):
        case = self.passing_case()
        report = self.harness.run_suite(
            [case],
            repo_root=REPO_ROOT,
            base_sha="a" * 40,
            head_sha="b" * 40,
            repeat=2,
            jobs=2,
        )

        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["summary"], {"passed": 2, "failed": 0, "total": 2})
        self.assertEqual(len(report["results"]), 2)
        json.dumps(report)


if __name__ == "__main__":
    unittest.main()
