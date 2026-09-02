import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "tooling" / "install" / "manager.py"


def load_manager():
    spec = importlib.util.spec_from_file_location("manifest_installer", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ManifestInstallerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager = load_manager()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.dist = self.root / "dist"
        self.target = self.root / "target with spaces"

    def write_dist(self, version: str, files: dict[str, str]) -> None:
        runtime_root = self.dist / "codex"
        runtime_root.mkdir(parents=True, exist_ok=True)
        for existing in sorted(path for path in runtime_root.rglob("*") if path.is_file()):
            existing.unlink()
        for relative, content in files.items():
            path = runtime_root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        report = {
            "schema_version": 1,
            "distribution": {"name": "skillz-claude", "version": version},
            "artifacts": [
                {
                    "provider": "codex",
                    "artifact_id": relative.replace("/", "-"),
                    "type": "skill",
                    "status": "supported",
                    "output": f"codex/{relative}",
                }
                for relative in sorted(files)
            ],
            "packages": [],
        }
        (self.dist / "build-report.json").write_text(json.dumps(report), encoding="utf-8")

    def test_fresh_install_writes_hashed_relative_manifest(self):
        self.write_dist("6.1.0-dev.1", {"skills/probe/SKILL.md": "probe\n"})

        result = self.manager.install_bundle(self.dist, self.target, "codex", mode="install")

        manifest = json.loads((self.target / ".skillz" / "install-manifest.json").read_text())
        self.assertEqual(result["status"], "installed")
        self.assertEqual(manifest["release"], "6.1.0-dev.1")
        self.assertEqual(manifest["runtime"], "codex")
        self.assertEqual(manifest["files"][0]["path"], "skills/probe/SKILL.md")
        self.assertEqual(manifest["files"][0]["source_hash"], manifest["files"][0]["installed_hash"])
        self.assertNotIn(str(self.root), json.dumps(manifest))

    def test_dry_run_does_not_create_target(self):
        self.write_dist("6.1.0-dev.1", {"skills/probe/SKILL.md": "probe\n"})

        result = self.manager.install_bundle(
            self.dist, self.target, "codex", mode="install", dry_run=True
        )

        self.assertEqual(result["status"], "dry-run")
        self.assertFalse(self.target.exists())

    def test_update_then_restore_recovers_previous_release_and_user_file(self):
        self.write_dist("6.1.0-dev.1", {"skills/probe/SKILL.md": "v1\n"})
        self.manager.install_bundle(self.dist, self.target, "codex", mode="install")
        user_file = self.target / "user-notes.md"
        user_file.write_text("mine\n", encoding="utf-8")
        self.write_dist("6.1.0-dev.2", {"skills/probe/SKILL.md": "v2\n"})
        self.manager.install_bundle(self.dist, self.target, "codex", mode="update")

        restored = self.manager.restore_target(self.target)

        manifest = json.loads((self.target / ".skillz" / "install-manifest.json").read_text())
        self.assertEqual(restored["status"], "restored")
        self.assertEqual(manifest["release"], "6.1.0-dev.1")
        self.assertEqual((self.target / "skills/probe/SKILL.md").read_text(), "v1\n")
        self.assertEqual(user_file.read_text(), "mine\n")

    def test_restore_recovers_artifact_removed_by_update(self):
        self.write_dist(
            "6.1.0-dev.1",
            {"skills/keep/SKILL.md": "keep\n", "skills/removed/SKILL.md": "restore-me\n"},
        )
        self.manager.install_bundle(self.dist, self.target, "codex", mode="install")
        self.write_dist("6.1.0-dev.2", {"skills/keep/SKILL.md": "keep\n"})
        self.manager.install_bundle(self.dist, self.target, "codex", mode="update")
        self.assertFalse((self.target / "skills/removed/SKILL.md").exists())

        self.manager.restore_target(self.target)

        self.assertEqual(
            (self.target / "skills/removed/SKILL.md").read_text(),
            "restore-me\n",
        )

    def test_update_allows_explicit_downgrade(self):
        self.write_dist("6.1.0-dev.2", {"skills/probe/SKILL.md": "newer\n"})
        self.manager.install_bundle(self.dist, self.target, "codex", mode="install")
        self.write_dist("6.1.0-dev.1", {"skills/probe/SKILL.md": "older\n"})

        result = self.manager.install_bundle(self.dist, self.target, "codex", mode="update")

        self.assertEqual(result["release"], "6.1.0-dev.1")
        self.assertEqual((self.target / "skills/probe/SKILL.md").read_text(), "older\n")

    def test_modified_owned_file_blocks_update_and_uninstall(self):
        self.write_dist("6.1.0-dev.1", {"skills/probe/SKILL.md": "owned\n"})
        self.manager.install_bundle(self.dist, self.target, "codex", mode="install")
        managed = self.target / "skills/probe/SKILL.md"
        managed.write_text("locally modified\n", encoding="utf-8")

        with self.assertRaisesRegex(self.manager.InstallConflict, "modified"):
            self.manager.install_bundle(self.dist, self.target, "codex", mode="update")
        with self.assertRaisesRegex(self.manager.InstallConflict, "modified"):
            self.manager.uninstall_target(self.target)
        self.assertEqual(managed.read_text(), "locally modified\n")

    def test_conflict_preflight_keeps_all_other_files_unchanged(self):
        self.write_dist(
            "6.1.0-dev.1",
            {"skills/a/SKILL.md": "a1\n", "skills/z/SKILL.md": "z1\n"},
        )
        self.manager.install_bundle(self.dist, self.target, "codex", mode="install")
        (self.target / "skills/z/SKILL.md").write_text("user-z\n", encoding="utf-8")
        self.write_dist(
            "6.1.0-dev.2",
            {"skills/a/SKILL.md": "a2\n", "skills/z/SKILL.md": "z2\n"},
        )

        with self.assertRaises(self.manager.InstallConflict):
            self.manager.install_bundle(self.dist, self.target, "codex", mode="update")

        self.assertEqual((self.target / "skills/a/SKILL.md").read_text(), "a1\n")
        self.assertEqual((self.target / "skills/z/SKILL.md").read_text(), "user-z\n")

    def test_identical_unowned_file_is_not_silently_adopted(self):
        self.write_dist("6.1.0-dev.1", {"skills/probe/SKILL.md": "same\n"})
        unowned = self.target / "skills/probe/SKILL.md"
        unowned.parent.mkdir(parents=True)
        unowned.write_text("same\n", encoding="utf-8")

        with self.assertRaisesRegex(self.manager.InstallConflict, "unexpected"):
            self.manager.install_bundle(self.dist, self.target, "codex", mode="install")

    def test_uninstall_removes_only_manifest_owned_files(self):
        self.write_dist("6.1.0-dev.1", {"skills/probe/SKILL.md": "owned\n"})
        self.manager.install_bundle(self.dist, self.target, "codex", mode="install")
        user_file = self.target / "skills/user/SKILL.md"
        user_file.parent.mkdir(parents=True)
        user_file.write_text("user\n", encoding="utf-8")

        dry_run = self.manager.uninstall_target(self.target, dry_run=True)
        result = self.manager.uninstall_target(self.target)

        self.assertEqual(dry_run["status"], "dry-run")
        self.assertEqual(result["status"], "uninstalled")
        self.assertFalse((self.target / "skills/probe/SKILL.md").exists())
        self.assertEqual(user_file.read_text(), "user\n")

    def test_broken_symlink_at_managed_path_is_a_conflict(self):
        self.write_dist("6.1.0-dev.1", {"skills/probe/SKILL.md": "owned\n"})
        path = self.target / "skills/probe/SKILL.md"
        path.parent.mkdir(parents=True)
        path.symlink_to(self.root / "missing")

        with self.assertRaisesRegex(self.manager.InstallConflict, "unverifiable"):
            self.manager.install_bundle(self.dist, self.target, "codex", mode="install")

    def test_symlinked_state_directory_is_a_conflict(self):
        self.write_dist("6.1.0-dev.1", {"skills/probe/SKILL.md": "owned\n"})
        self.target.mkdir(parents=True)
        (self.target / ".skillz").symlink_to(self.root / "outside-state")

        with self.assertRaisesRegex(self.manager.InstallConflict, "state symlink"):
            self.manager.install_bundle(self.dist, self.target, "codex", mode="install")

    def test_symlinked_target_is_a_conflict(self):
        self.write_dist("6.1.0-dev.1", {"skills/probe/SKILL.md": "owned\n"})
        self.target.symlink_to(self.root / "outside-target")

        with self.assertRaisesRegex(self.manager.InstallConflict, "target symlink"):
            self.manager.install_bundle(self.dist, self.target, "codex", mode="install")

    def test_bundle_symlink_is_rejected_even_when_broken(self):
        self.write_dist("6.1.0-dev.1", {"skills/probe/SKILL.md": "owned\n"})
        (self.dist / "codex" / "broken-link").symlink_to(self.root / "missing-source")

        with self.assertRaisesRegex(self.manager.InstallError, "bundle contains a symlink"):
            self.manager.install_bundle(self.dist, self.target, "codex", mode="install")

    def test_bundle_cannot_write_reserved_installer_state(self):
        self.write_dist("6.1.0-dev.1", {".skillz/install-manifest.json": "spoofed\n"})

        with self.assertRaisesRegex(self.manager.InstallError, "reserved installer state"):
            self.manager.install_bundle(self.dist, self.target, "codex", mode="install")

    def test_doctor_distinguishes_file_states_and_missing_runtime(self):
        files = {
            "skills/missing/SKILL.md": "missing\n",
            "skills/modified/SKILL.md": "modified\n",
            "skills/unverifiable/SKILL.md": "unverifiable\n",
            "skills/orphaned/SKILL.md": "orphaned\n",
        }
        self.write_dist("6.1.0-dev.1", files)
        self.manager.install_bundle(self.dist, self.target, "codex", mode="install")
        (self.target / "skills/missing/SKILL.md").unlink()
        (self.target / "skills/modified/SKILL.md").write_text("changed\n", encoding="utf-8")
        unverifiable = self.target / "skills/unverifiable/SKILL.md"
        unverifiable.unlink()
        unverifiable.symlink_to(self.root / "missing-target")
        self.write_dist(
            "6.1.0-dev.2",
            {
                "skills/missing/SKILL.md": "missing\n",
                "skills/modified/SKILL.md": "modified\n",
                "skills/unverifiable/SKILL.md": "unverifiable\n",
                "skills/unexpected/SKILL.md": "expected-new\n",
            },
        )
        unexpected = self.target / "skills/unexpected/SKILL.md"
        unexpected.parent.mkdir(parents=True, exist_ok=True)
        unexpected.write_text("user collision\n", encoding="utf-8")

        report = self.manager.doctor_target(
            self.dist,
            self.target,
            "codex",
            runtime_binary="definitely-missing-skillz-runtime",
        )

        states = {item["path"]: item["state"] for item in report["files"]}
        self.assertEqual(states["skills/missing/SKILL.md"], "missing")
        self.assertEqual(states["skills/modified/SKILL.md"], "modified")
        self.assertEqual(states["skills/unverifiable/SKILL.md"], "unverifiable")
        self.assertEqual(states["skills/orphaned/SKILL.md"], "orphaned")
        self.assertEqual(states["skills/unexpected/SKILL.md"], "unexpected")
        self.assertFalse(report["runtime"]["detected"])
        self.assertEqual(report["status"], "broken")

    def test_restore_dry_run_keeps_current_release(self):
        self.write_dist("6.1.0-dev.1", {"skills/probe/SKILL.md": "v1\n"})
        self.manager.install_bundle(self.dist, self.target, "codex", mode="install")
        self.write_dist("6.1.0-dev.2", {"skills/probe/SKILL.md": "v2\n"})
        self.manager.install_bundle(self.dist, self.target, "codex", mode="update")

        result = self.manager.restore_target(self.target, dry_run=True)

        self.assertEqual(result["status"], "dry-run")
        self.assertEqual((self.target / "skills/probe/SKILL.md").read_text(), "v2\n")

    def test_doctor_marks_release_drift_partial(self):
        self.write_dist("6.1.0-dev.1", {"skills/probe/SKILL.md": "same\n"})
        self.manager.install_bundle(self.dist, self.target, "codex", mode="install")
        self.write_dist("6.1.0-dev.2", {"skills/probe/SKILL.md": "same\n"})

        report = self.manager.doctor_target(
            self.dist,
            self.target,
            "codex",
            runtime_binary="true",
        )

        self.assertEqual(report["status"], "partial")
        self.assertTrue(report["release_drift"])

    def test_backups_are_bounded(self):
        for index in range(1, 5):
            self.write_dist(
                f"6.1.0-dev.{index}",
                {"skills/probe/SKILL.md": f"v{index}\n"},
            )
            self.manager.install_bundle(
                self.dist,
                self.target,
                "codex",
                mode="install" if index == 1 else "update",
                backup_limit=2,
            )

        backups = [
            path
            for path in (self.target / ".skillz/backups").iterdir()
            if path.is_dir()
        ]
        self.assertEqual(len(backups), 2)

    def test_skillz_doctor_emits_json_and_nonzero_for_broken_target(self):
        self.write_dist("6.1.0-dev.1", {"skills/probe/SKILL.md": "probe\n"})

        completed = subprocess.run(
            [
                str(REPO_ROOT / "bin" / "skillz"),
                "--json",
                "doctor",
                "--dist-root",
                str(self.dist),
                "--runtime",
                "codex",
                "--target",
                str(self.target),
                "--runtime-binary",
                "definitely-missing-skillz-runtime",
            ],
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        payload = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(payload["status"], "broken")
        self.assertIn("summary", payload)


if __name__ == "__main__":
    unittest.main()
