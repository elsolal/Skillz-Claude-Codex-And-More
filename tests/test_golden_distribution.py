import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "tooling" / "testing" / "golden_distribution.py"


def load_golden():
    spec = importlib.util.spec_from_file_location("golden_distribution", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class GoldenDistributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.golden = load_golden()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.dist = self.root / "dist"
        shutil.copytree(REPO_ROOT / "dist", self.dist)

    def test_snapshot_captures_provider_files_modes_manifests_and_aliases(self):
        snapshot = self.golden.snapshot_distribution(self.dist)

        self.assertEqual(snapshot["schema_version"], 1)
        self.assertEqual(snapshot["distribution"]["version"], "6.1.0-rc.1")
        self.assertIn("codex", snapshot["providers"])
        codex = snapshot["providers"]["codex"]
        self.assertTrue(any(item["path"] == ".codex-plugin/plugin.json" for item in codex["files"]))
        self.assertTrue(any(item["alias"] == "quick-fix" for item in codex["aliases"]))
        self.assertTrue(any(item["frontmatter"].get("name") for item in codex["skills"]))

    def test_compare_reports_removed_added_and_modified_files(self):
        expected = self.golden.snapshot_distribution(self.dist)
        (self.dist / "codex" / "skills" / "project-probe" / "SKILL.md").unlink()
        (self.dist / "codex" / "prompts" / "quick-fix.md").write_text("changed\n")
        (self.dist / "codex" / "extra.txt").write_text("extra\n")

        actual = self.golden.snapshot_distribution(self.dist)
        differences = self.golden.compare_snapshots(expected, actual)

        self.assertTrue(any(item.startswith("removed:") for item in differences))
        self.assertTrue(any(item.startswith("modified:") for item in differences))
        self.assertTrue(any(item.startswith("added:") for item in differences))

    def test_golden_update_requires_explicit_review_approval(self):
        snapshot = self.golden.snapshot_distribution(self.dist)
        output = self.root / "golden.json"

        with self.assertRaisesRegex(self.golden.GoldenError, "approval"):
            self.golden.write_golden(output, snapshot, approved=False)
        self.golden.write_golden(output, snapshot, approved=True)

        self.assertEqual(json.loads(output.read_text()), snapshot)

    def test_neutral_contracts_do_not_contain_claude_specific_paths(self):
        findings = self.golden.scan_neutral_contracts(REPO_ROOT / "core" / "contracts")

        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
