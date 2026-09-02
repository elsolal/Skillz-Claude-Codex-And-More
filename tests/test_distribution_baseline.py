import importlib.util
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "capture_distribution_baseline.py"
GOLDEN_PATH = REPO_ROOT / "docs" / "compatibility" / "golden" / "legacy-v6-distribution.json"
BASELINE_PATH = REPO_ROOT / "docs" / "compatibility" / "baseline-2026-09-01.yaml"
SPEC = importlib.util.spec_from_file_location("capture_distribution_baseline", MODULE_PATH)
baseline = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(baseline)


class DistributionBaselineTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def write(self, relative_path: str, content: str) -> Path:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def track(self, *relative_paths: str) -> None:
        subprocess.run(["git", "add", "--", *relative_paths], cwd=self.root, check=True)

    def test_capture_includes_only_tracked_distribution_surfaces(self):
        self.write(".claude/skills/demo/SKILL.md", "# Demo\n")
        self.write(".codex/prompts/demo.md", "Run demo\n")
        self.write("install.sh", "#!/bin/sh\n")
        self.write(".codex/hooks.json", '{"user_owned": true}\n')
        self.write(".agents/verification.yaml", "commands: {}\n")
        self.write("scripts/capture_distribution_baseline.py", "# control plane\n")
        self.track(
            ".claude/skills/demo/SKILL.md",
            ".codex/prompts/demo.md",
            ".agents/verification.yaml",
            "install.sh",
            "scripts/capture_distribution_baseline.py",
        )

        result = baseline.capture_repository(self.root)
        paths = [artifact["path"] for artifact in result["artifacts"]]

        self.assertEqual(
            paths,
            [
                ".claude/skills/demo/SKILL.md",
                ".codex/prompts/demo.md",
                "install.sh",
            ],
        )
        self.assertNotIn(".codex/hooks.json", paths)
        self.assertNotIn(".agents/verification.yaml", paths)
        self.assertNotIn("scripts/capture_distribution_baseline.py", paths)
        self.assertTrue(all(artifact["ownership"] == "skillz" for artifact in result["artifacts"]))

    def test_capture_is_deterministic_and_records_symlink_targets(self):
        self.write(".claude/skills/demo/SKILL.md", "# Demo\n")
        os.symlink(".claude/skills", self.root / "skills")
        self.track(".claude/skills/demo/SKILL.md", "skills")

        first = baseline.render_json(baseline.capture_repository(self.root))
        second = baseline.render_json(baseline.capture_repository(self.root))
        payload = json.loads(first)
        symlink = next(item for item in payload["artifacts"] if item["path"] == "skills")

        self.assertEqual(first, second)
        self.assertEqual(symlink["type"], "symlink")
        self.assertEqual(symlink["target"], ".claude/skills")

    def test_capture_rejects_absolute_symlink_targets(self):
        os.symlink(str(self.root / "outside"), self.root / "skills")
        self.track("skills")

        with self.assertRaisesRegex(baseline.BaselineError, "absolute symlink target"):
            baseline.capture_repository(self.root)

    def test_rendered_snapshot_contains_no_absolute_checkout_path(self):
        self.write("AGENTS.md", "# Agent instructions\n")
        self.track("AGENTS.md")

        rendered = baseline.render_json(baseline.capture_repository(self.root))

        self.assertNotIn(str(self.root), rendered)
        self.assertTrue(rendered.endswith("\n"))

    def test_check_snapshot_reports_drift_without_mutating_the_file(self):
        self.write("README.md", "# Before\n")
        self.track("README.md")
        snapshot = self.root / "golden.json"
        snapshot.write_text(
            baseline.render_json(baseline.capture_repository(self.root)),
            encoding="utf-8",
        )
        original = snapshot.read_bytes()
        self.write("README.md", "# After\n")

        differences = baseline.check_snapshot(
            baseline.capture_repository(self.root),
            snapshot,
        )

        self.assertIn("README.md", "\n".join(differences))
        self.assertEqual(snapshot.read_bytes(), original)

    def test_committed_golden_is_a_well_formed_legacy_snapshot(self):
        payload = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
        artifacts = payload["artifacts"]
        paths = [artifact["path"] for artifact in artifacts]

        self.assertEqual(payload["baseline_id"], "legacy-v6")
        self.assertEqual(len(artifacts), 623)
        self.assertEqual(paths, sorted(paths))
        self.assertEqual(len(paths), len(set(paths)))
        self.assertTrue(
            all(
                artifact["ownership"] == "skillz"
                and artifact["type"] in {"file", "symlink"}
                for artifact in artifacts
            )
        )

    def test_baseline_metadata_hash_matches_committed_golden(self):
        metadata = BASELINE_PATH.read_text(encoding="utf-8")
        match = re.search(r'^  sha256: "([0-9a-f]{64})"$', metadata, re.MULTILINE)

        self.assertIsNotNone(match)
        self.assertEqual(
            match.group(1),
            hashlib.sha256(GOLDEN_PATH.read_bytes()).hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
