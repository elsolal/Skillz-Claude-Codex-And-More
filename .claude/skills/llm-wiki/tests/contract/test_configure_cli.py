from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = SKILL_ROOT.parents[2]
FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "manifest-v1" / "valid.json"
EXPECTED = SKILL_ROOT / "expected_outputs" / "memory"


class ConfigureCliContractTests(unittest.TestCase):
    def run_process(self, *arguments: str, cwd: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            list(arguments),
            cwd=cwd,
            check=False,
            text=True,
            capture_output=True,
        )

    def run_git(self, cwd: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return self.run_process("git", *arguments, cwd=cwd)

    def run_cli(self, cwd: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(SKILL_ROOT)
        return subprocess.run(
            [sys.executable, "-m", "memory_cli", "configure", *arguments],
            cwd=cwd,
            env=environment,
            check=False,
            text=True,
            capture_output=True,
        )

    def make_repo(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temp_dir = tempfile.TemporaryDirectory()
        repo = Path(temp_dir.name) / "repo"
        repo.mkdir()
        self.assertEqual(self.run_git(repo, "init", "-b", "main").returncode, 0)
        self.assertEqual(self.run_git(repo, "config", "user.email", "tests@example.test").returncode, 0)
        self.assertEqual(self.run_git(repo, "config", "user.name", "Tests").returncode, 0)
        (repo / ".agents").mkdir()
        (repo / ".agents" / "memory.yaml").write_text(FIXTURE.read_text(), encoding="utf-8")
        self.assertEqual(self.run_git(repo, "add", ".agents/memory.yaml").returncode, 0)
        self.assertEqual(self.run_git(repo, "commit", "-m", "fixture").returncode, 0)
        return temp_dir, repo

    def make_vault(self, root: Path, *, complete: bool = True) -> Path:
        vault = root / "vault"
        (vault / "wiki" / "entities").mkdir(parents=True)
        (vault / "wiki" / "concepts").mkdir(parents=True)
        (vault / "wiki" / "entities" / "skillz-claude.md").write_text("# Skillz-Claude\n")
        if complete:
            (vault / "wiki" / "concepts" / "project-memory-workflow.md").write_text(
                "# Project memory workflow\n"
            )
        return vault

    def configure(self, repo: Path, vault: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return self.run_cli(repo, "--store", f"project={vault}", *arguments)

    def test_ready_configuration_creates_private_ignored_files_without_leaking_paths(self) -> None:
        temp_dir, repo = self.make_repo()
        self.addCleanup(temp_dir.cleanup)
        vault = self.make_vault(Path(temp_dir.name))

        result = self.configure(repo, vault, "--json")
        output = json.loads(result.stdout)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            list(output),
            ["schema_version", "command", "status", "project_id", "event_id", "data", "warnings", "errors"],
        )
        self.assertEqual(output["command"], "configure")
        self.assertEqual(output["status"], "ready")
        self.assertEqual(output["project_id"], "skillz-claude")
        self.assertNotIn(str(vault), result.stdout)
        self.assertEqual(output["data"]["principal"]["role"], "collaborator")
        self.assertEqual(output["data"]["configured_stores"], ["project"])
        self.assertEqual(output, json.loads((EXPECTED / "configure-ready.json").read_text()))

        projection_path = repo / ".agents" / "memory.local.json"
        claude_pointer = repo / ".claude" / "project-memory.md"
        agents_pointer = repo / ".agents" / "project-memory.md"
        projection = json.loads(projection_path.read_text(encoding="utf-8"))

        self.assertEqual(projection["stores"]["project"]["root"], str(vault.resolve()))
        self.assertEqual(projection["principal"]["role"], "collaborator")
        self.assertIn("Managed by skillz-memory", claude_pointer.read_text(encoding="utf-8"))
        self.assertIn("Managed by skillz-memory", agents_pointer.read_text(encoding="utf-8"))
        for local_path in (projection_path, claude_pointer, agents_pointer):
            self.assertEqual(stat.S_IMODE(local_path.stat().st_mode), 0o600)
            ignored = self.run_git(repo, "check-ignore", "-q", str(local_path.relative_to(repo)))
            self.assertEqual(ignored.returncode, 0, local_path)
        self.assertEqual(self.run_git(repo, "status", "--porcelain").stdout, "")

    def test_explicit_owner_role_is_persisted_without_granting_additional_configuration(self) -> None:
        temp_dir, repo = self.make_repo()
        self.addCleanup(temp_dir.cleanup)
        vault = self.make_vault(Path(temp_dir.name))

        result = self.configure(repo, vault, "--json", "--role", "owner")
        output = json.loads(result.stdout)
        projection = json.loads((repo / ".agents" / "memory.local.json").read_text())

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output["data"]["principal"]["role"], "owner")
        self.assertEqual(projection["principal"]["role"], "owner")

    def test_explain_local_paths_reveals_paths_only_when_explicitly_requested(self) -> None:
        temp_dir, repo = self.make_repo()
        self.addCleanup(temp_dir.cleanup)
        vault = self.make_vault(Path(temp_dir.name))

        result = self.configure(repo, vault, "--json", "--explain-local-paths")
        output = json.loads(result.stdout)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output["data"]["local_paths"]["stores"]["project"], str(vault.resolve()))

    def test_degraded_configuration_is_written_and_reports_relative_missing_pages(self) -> None:
        temp_dir, repo = self.make_repo()
        self.addCleanup(temp_dir.cleanup)
        vault = self.make_vault(Path(temp_dir.name), complete=False)

        result = self.configure(repo, vault, "--json")
        output = json.loads(result.stdout)

        self.assertEqual(result.returncode, 10, result.stderr)
        self.assertEqual(output["status"], "degraded")
        self.assertTrue((repo / ".agents" / "memory.local.json").is_file())
        warning = output["warnings"][0]
        self.assertEqual(warning["code"], "missing_entry_pages")
        self.assertEqual(warning["paths"], ["wiki/concepts/project-memory-workflow.md"])
        self.assertNotIn(str(vault), result.stdout)
        self.assertEqual(output, json.loads((EXPECTED / "configure-degraded.json").read_text()))

    def test_repeated_configuration_preserves_identical_files_and_mtimes(self) -> None:
        temp_dir, repo = self.make_repo()
        self.addCleanup(temp_dir.cleanup)
        vault = self.make_vault(Path(temp_dir.name))

        first = self.configure(repo, vault, "--json")
        self.assertEqual(first.returncode, 0, first.stderr)
        local_paths = (
            repo / ".agents" / "memory.local.json",
            repo / ".claude" / "project-memory.md",
            repo / ".agents" / "project-memory.md",
        )
        snapshots = [(path.read_bytes(), path.stat().st_mtime_ns) for path in local_paths]
        time.sleep(0.01)

        second = self.configure(repo, vault, "--json")

        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(
            [(path.read_bytes(), path.stat().st_mtime_ns) for path in local_paths],
            snapshots,
        )
        exclude_path = Path(
            self.run_git(repo, "rev-parse", "--path-format=absolute", "--git-path", "info/exclude")
            .stdout.strip()
        )
        exclude_content = exclude_path.read_text(encoding="utf-8")
        for pattern in (
            ".agents/memory.local.json",
            ".claude/project-memory.md",
            ".agents/project-memory.md",
        ):
            self.assertEqual(exclude_content.splitlines().count(pattern), 1)

    def test_unmanaged_pointer_is_preserved_unless_replacement_is_explicit(self) -> None:
        temp_dir, repo = self.make_repo()
        self.addCleanup(temp_dir.cleanup)
        vault = self.make_vault(Path(temp_dir.name))
        pointer = repo / ".claude" / "project-memory.md"
        pointer.parent.mkdir()
        pointer.write_text("# My custom pointer\n", encoding="utf-8")

        blocked = self.configure(repo, vault, "--json")
        blocked_output = json.loads(blocked.stdout)

        self.assertEqual(blocked.returncode, 30)
        self.assertEqual(blocked_output["status"], "blocked")
        self.assertEqual(blocked_output["errors"][0]["code"], "unmanaged_pointer")
        self.assertEqual(pointer.read_text(encoding="utf-8"), "# My custom pointer\n")
        self.assertFalse((repo / ".agents" / "memory.local.json").exists())

        replaced = self.configure(repo, vault, "--json", "--replace-managed")

        self.assertEqual(replaced.returncode, 0, replaced.stderr)
        self.assertIn("Managed by skillz-memory", pointer.read_text(encoding="utf-8"))

    def test_entry_page_symlink_cannot_escape_the_store_root(self) -> None:
        temp_dir, repo = self.make_repo()
        self.addCleanup(temp_dir.cleanup)
        vault = self.make_vault(Path(temp_dir.name))
        outside = Path(temp_dir.name) / "outside.md"
        outside.write_text("outside\n", encoding="utf-8")
        page = vault / "wiki" / "concepts" / "project-memory-workflow.md"
        page.unlink()
        page.symlink_to(outside)

        result = self.configure(repo, vault, "--json")
        output = json.loads(result.stdout)

        self.assertEqual(result.returncode, 30)
        self.assertEqual(output["errors"][0]["code"], "entry_page_outside_store")
        self.assertNotIn(str(vault), result.stdout)
        self.assertFalse((repo / ".agents" / "memory.local.json").exists())

    def test_linked_worktree_uses_common_git_exclude_and_stays_clean(self) -> None:
        temp_dir, repo = self.make_repo()
        self.addCleanup(temp_dir.cleanup)
        vault = self.make_vault(Path(temp_dir.name))
        worktree = Path(temp_dir.name) / "worktree"
        self.assertEqual(self.run_git(repo, "branch", "feature/configure").returncode, 0)
        added = self.run_git(repo, "worktree", "add", str(worktree), "feature/configure")
        self.assertEqual(added.returncode, 0, added.stderr)

        result = self.configure(worktree, vault, "--json")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.run_git(worktree, "status", "--porcelain").stdout, "")
        exclude_path = Path(
            self.run_git(worktree, "rev-parse", "--path-format=absolute", "--git-path", "info/exclude")
            .stdout.strip()
        )
        self.assertIn(".agents/memory.local.json", exclude_path.read_text(encoding="utf-8"))

    def test_legacy_pointer_script_delegates_to_configure(self) -> None:
        temp_dir, repo = self.make_repo()
        self.addCleanup(temp_dir.cleanup)
        vault = self.make_vault(Path(temp_dir.name))

        result = self.run_process(
            str(REPO_ROOT / "scripts" / "create-project-memory-pointer.sh"),
            "--project-dir",
            str(repo),
            "--vault-path",
            str(vault),
            "--project-name",
            "Skillz-Claude",
            "--memory-repo",
            "https://github.com/elsolal/elsolal-memory.git",
            "--qmd-collection",
            "elsolal-wiki",
            "--start-page",
            "wiki/entities/skillz-claude.md",
            cwd=repo,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("deprecated", result.stderr.lower())
        self.assertTrue((repo / ".agents" / "memory.local.json").is_file())
        self.assertIn("Managed by skillz-memory", (repo / ".claude" / "project-memory.md").read_text())


if __name__ == "__main__":
    unittest.main()
