from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[2]
EXPECTED = SKILL_ROOT / "expected_outputs" / "memory"


class DoctorCliContractTests(unittest.TestCase):
    def run_process(
        self,
        *arguments: str,
        cwd: Path,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            list(arguments),
            cwd=cwd,
            env=env,
            check=False,
            text=True,
            capture_output=True,
        )

    def run_git(self, cwd: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return self.run_process("git", *arguments, cwd=cwd)

    def run_cli(
        self,
        cwd: Path,
        *arguments: str,
        path_prefix: Path | None = None,
        extra_env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(SKILL_ROOT)
        if path_prefix is not None:
            environment["PATH"] = f"{path_prefix}{os.pathsep}{environment['PATH']}"
        if extra_env:
            environment.update(extra_env)
        return subprocess.run(
            [sys.executable, "-m", "memory_cli", "doctor", *arguments],
            cwd=cwd,
            env=environment,
            check=False,
            text=True,
            capture_output=True,
        )

    def manifest_payload(
        self,
        *,
        project_id: str = "skillz-claude",
        collection: str = "elsolal-wiki",
    ) -> dict[str, object]:
        return {
            "schema_version": 1,
            "project": {
                "id": project_id,
                "name": project_id.replace("-", " ").title(),
                "owner": "Tests",
            },
            "stores": {
                "project": {
                    "remote": "https://example.test/memory.git",
                    "collection": collection,
                    "entry_pages": [
                        "wiki/entities/project.md",
                        "wiki/concepts/workflow.md",
                    ],
                }
            },
            "fallbacks": [],
            "budgets": {
                "minimal": {"target_tokens": 800, "hard_tokens": 1200},
                "project": {"target_tokens": 2500, "hard_tokens": 4000},
                "historical": {"target_tokens": 6000, "hard_tokens": 9000},
            },
            "policy": {
                "semantic_retrieval": "explicit",
                "full_index_fallback": True,
                "retention_days": 30,
            },
            "golden": {
                "visible_path": ".agents/memory/golden.json",
                "quality_rubric": ".agents/memory/quality-rubric.json",
                "start_question": "What should I know before working on this project?",
            },
        }

    def make_configured_project(
        self,
        *,
        project_id: str = "skillz-claude",
        collection: str = "elsolal-wiki",
    ) -> tuple[tempfile.TemporaryDirectory[str], Path, Path]:
        temp_dir = tempfile.TemporaryDirectory()
        root = Path(temp_dir.name)
        repo = root / "repo"
        vault = root / "vault"
        (repo / ".agents").mkdir(parents=True)
        (vault / "wiki" / "entities").mkdir(parents=True)
        (vault / "wiki" / "concepts").mkdir(parents=True)
        (vault / "wiki" / "entities" / "project.md").write_text("# Project\n")
        (vault / "wiki" / "concepts" / "workflow.md").write_text("# Workflow\n")
        (repo / ".agents" / "memory.yaml").write_text(
            json.dumps(self.manifest_payload(project_id=project_id, collection=collection)),
            encoding="utf-8",
        )
        self.assertEqual(self.run_git(repo, "init", "-b", "main").returncode, 0)
        self.assertEqual(self.run_git(repo, "config", "user.email", "tests@example.test").returncode, 0)
        self.assertEqual(self.run_git(repo, "config", "user.name", "Tests").returncode, 0)
        self.assertEqual(self.run_git(repo, "add", ".agents/memory.yaml").returncode, 0)
        self.assertEqual(self.run_git(repo, "commit", "-m", "fixture").returncode, 0)

        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(SKILL_ROOT)
        configured = subprocess.run(
            [
                sys.executable,
                "-m",
                "memory_cli",
                "configure",
                "--store",
                f"project={vault}",
                "--json",
            ],
            cwd=repo,
            env=environment,
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(configured.returncode, 0, configured.stdout + configured.stderr)
        return temp_dir, repo, vault

    def make_qmd(
        self,
        root: Path,
        *,
        collection: str = "elsolal-wiki",
        age: str = "just now",
        version: str = "0.9.0",
        malformed_status: bool = False,
        files: int = 2,
    ) -> tuple[Path, Path]:
        binary_dir = root / "bin"
        binary_dir.mkdir()
        invocation_log = root / "qmd-invocations.log"
        binary = binary_dir / "qmd"
        status_output = (
            "    echo 'malformed status'\n"
            if malformed_status
            else (
                "    echo 'QMD Status'\n"
                "    echo 'Collections'\n"
                f"    echo '  {collection} (qmd://{collection}/)'\n"
                "    echo '    Pattern:  **/*.md'\n"
                f"    echo '    Files:    {files} (updated {age})'\n"
            )
        )
        binary.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            f"printf '%s\\n' \"$*\" >> {invocation_log!s}\n"
            "case \"${1:-}\" in\n"
            f"  --version) echo 'qmd {version} (fixture)' ;;\n"
            "  status)\n"
            + status_output
            +
            "    ;;\n"
            "  *) exit 97 ;;\n"
            "esac\n",
            encoding="utf-8",
        )
        binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
        return binary_dir, invocation_log

    def make_git_proxy(self, root: Path, binary_dir: Path, *, remote_exit: int = 0) -> Path:
        real_git = shutil.which("git")
        self.assertIsNotNone(real_git)
        invocation_log = root / "git-invocations.log"
        binary = binary_dir / "git"
        binary.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            f"printf '%s\\n' \"$*\" >> {invocation_log!s}\n"
            "if [ \"${1:-}\" = 'ls-remote' ]; then\n"
            f"  exit {remote_exit}\n"
            "fi\n"
            f"exec {real_git} \"$@\"\n",
            encoding="utf-8",
        )
        binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
        return invocation_log

    def test_ready_json_is_stable_and_nominal_run_is_read_only(self) -> None:
        temp_dir, repo, vault = self.make_configured_project()
        self.addCleanup(temp_dir.cleanup)
        binary_dir, invocation_log = self.make_qmd(Path(temp_dir.name))
        git_log = self.make_git_proxy(Path(temp_dir.name), binary_dir)
        observed_paths = (
            repo / ".agents" / "memory.local.json",
            repo / ".claude" / "project-memory.md",
            repo / ".agents" / "project-memory.md",
            vault / "wiki" / "entities" / "project.md",
            vault / "wiki" / "concepts" / "workflow.md",
        )
        snapshots = [(path.read_bytes(), path.stat().st_mtime_ns) for path in observed_paths]
        refs_before = self.run_git(repo, "show-ref").stdout

        result = self.run_cli(repo, "--json", path_prefix=binary_dir)
        output = json.loads(result.stdout)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            list(output),
            ["schema_version", "command", "status", "project_id", "event_id", "data", "warnings", "errors"],
        )
        self.assertEqual(output["command"], "doctor")
        self.assertEqual(output["status"], "ready")
        self.assertEqual(output["project_id"], "skillz-claude")
        self.assertEqual(output["data"]["summary"], {"ready": 6, "total": 6})
        self.assertEqual(
            output["data"]["capabilities"],
            {"available_modes": ["minimal", "project", "historical"], "unavailable_modes": []},
        )
        self.assertEqual(
            output["data"]["start_question"],
            "What should I know before working on this project?",
        )
        self.assertEqual(output["warnings"], [])
        self.assertEqual(output["errors"], [])
        self.assertEqual(output, json.loads((EXPECTED / "doctor-ready.json").read_text()))
        self.assertNotIn(str(repo), result.stdout)
        self.assertNotIn(str(vault), result.stdout)
        self.assertEqual(
            [(path.read_bytes(), path.stat().st_mtime_ns) for path in observed_paths],
            snapshots,
        )
        self.assertEqual(self.run_git(repo, "show-ref").stdout, refs_before)
        self.assertEqual(invocation_log.read_text().splitlines(), ["--version", "status"])
        git_invocations = git_log.read_text().splitlines()
        self.assertFalse(any("fetch" in invocation for invocation in git_invocations))
        self.assertFalse(any("ls-remote" in invocation for invocation in git_invocations))

    def test_qmd_missing_is_degraded_with_copyable_install_and_available_modes(self) -> None:
        temp_dir, repo, _ = self.make_configured_project()
        self.addCleanup(temp_dir.cleanup)
        empty_path = Path(temp_dir.name) / "empty-bin"
        empty_path.mkdir()

        result = self.run_cli(
            repo,
            "--json",
            path_prefix=empty_path,
            extra_env={"SKILLZ_MEMORY_QMD": str(empty_path / "missing-qmd")},
        )
        output = json.loads(result.stdout)

        self.assertEqual(result.returncode, 10, result.stderr)
        self.assertEqual(output["status"], "degraded")
        self.assertEqual(
            output["data"]["capabilities"],
            {"available_modes": ["minimal", "project"], "unavailable_modes": ["historical"]},
        )
        self.assertEqual(output["warnings"][0]["code"], "qmd_missing")
        self.assertIn("bun install -g @tobilu/qmd", output["data"]["next_actions"])

    def test_missing_entry_page_is_blocked_with_priority_exit(self) -> None:
        temp_dir, repo, vault = self.make_configured_project()
        self.addCleanup(temp_dir.cleanup)
        binary_dir, _ = self.make_qmd(Path(temp_dir.name))
        (vault / "wiki" / "concepts" / "workflow.md").unlink()

        result = self.run_cli(repo, "--json", path_prefix=binary_dir)
        output = json.loads(result.stdout)

        self.assertEqual(result.returncode, 30, result.stderr)
        self.assertEqual(output["status"], "blocked")
        self.assertEqual(output["errors"][0]["code"], "missing_entry_pages")
        self.assertEqual(output["errors"][0]["paths"], ["wiki/concepts/workflow.md"])
        self.assertNotIn(str(vault), result.stdout)

    def test_invalid_projection_is_blocked_without_leaking_its_store(self) -> None:
        temp_dir, repo, vault = self.make_configured_project()
        self.addCleanup(temp_dir.cleanup)
        binary_dir, _ = self.make_qmd(Path(temp_dir.name))
        (repo / ".agents" / "memory.local.json").write_text("{invalid", encoding="utf-8")

        result = self.run_cli(repo, "--json", path_prefix=binary_dir)
        output = json.loads(result.stdout)

        self.assertEqual(result.returncode, 30, result.stderr)
        self.assertEqual(output["status"], "blocked")
        self.assertEqual(output["errors"][0]["code"], "projection_invalid")
        self.assertNotIn(str(vault), result.stdout)

    def test_unknown_or_stale_qmd_collection_is_degraded_with_exact_actions(self) -> None:
        temp_dir, repo, _ = self.make_configured_project()
        self.addCleanup(temp_dir.cleanup)
        binary_dir, _ = self.make_qmd(Path(temp_dir.name), collection="another-wiki")

        unknown = self.run_cli(repo, "--json", path_prefix=binary_dir)
        unknown_output = json.loads(unknown.stdout)

        self.assertEqual(unknown.returncode, 10, unknown.stderr)
        self.assertEqual(unknown_output["warnings"][0]["code"], "qmd_collection_unknown")

        temp_dir_2, repo_2, _ = self.make_configured_project()
        self.addCleanup(temp_dir_2.cleanup)
        binary_dir_2, _ = self.make_qmd(Path(temp_dir_2.name), age="2d ago")
        stale = self.run_cli(repo_2, "--json", path_prefix=binary_dir_2)
        stale_output = json.loads(stale.stdout)

        self.assertEqual(stale.returncode, 10, stale.stderr)
        self.assertEqual(stale_output["warnings"][0]["code"], "qmd_index_stale")
        self.assertEqual(
            stale_output["data"]["next_actions"],
            ["qmd update", "qmd embed", "memory doctor"],
        )

    def test_unsupported_or_malformed_qmd_output_is_degraded(self) -> None:
        for version, malformed in (("1.0.0", False), ("0.9.0", True)):
            with self.subTest(version=version, malformed=malformed):
                temp_dir, repo, _ = self.make_configured_project()
                self.addCleanup(temp_dir.cleanup)
                binary_dir, _ = self.make_qmd(
                    Path(temp_dir.name),
                    version=version,
                    malformed_status=malformed,
                )

                result = self.run_cli(repo, "--json", path_prefix=binary_dir)
                output = json.loads(result.stdout)

                self.assertEqual(result.returncode, 10, result.stderr)
                self.assertEqual(output["warnings"][0]["code"], "qmd_status_unavailable")

    def test_empty_collection_or_index_older_than_entry_pages_is_degraded(self) -> None:
        temp_dir, repo, _ = self.make_configured_project()
        self.addCleanup(temp_dir.cleanup)
        binary_dir, _ = self.make_qmd(Path(temp_dir.name), files=0)

        empty = self.run_cli(repo, "--json", path_prefix=binary_dir)
        empty_output = json.loads(empty.stdout)

        self.assertEqual(empty.returncode, 10, empty.stderr)
        self.assertEqual(empty_output["warnings"][0]["code"], "qmd_collection_empty")

        temp_dir_2, repo_2, _ = self.make_configured_project()
        self.addCleanup(temp_dir_2.cleanup)
        binary_dir_2, _ = self.make_qmd(Path(temp_dir_2.name), age="1h ago")
        behind_pages = self.run_cli(repo_2, "--json", path_prefix=binary_dir_2)
        behind_pages_output = json.loads(behind_pages.stdout)

        self.assertEqual(behind_pages.returncode, 10, behind_pages.stderr)
        self.assertEqual(behind_pages_output["warnings"][0]["code"], "qmd_index_stale")

    def test_missing_start_question_is_backward_compatible_but_degraded(self) -> None:
        temp_dir, repo, _ = self.make_configured_project()
        self.addCleanup(temp_dir.cleanup)
        binary_dir, _ = self.make_qmd(Path(temp_dir.name))
        manifest_path = repo / ".agents" / "memory.yaml"
        payload = json.loads(manifest_path.read_text())
        del payload["golden"]["start_question"]
        manifest_path.write_text(json.dumps(payload), encoding="utf-8")

        result = self.run_cli(repo, "--json", path_prefix=binary_dir)
        output = json.loads(result.stdout)

        self.assertEqual(result.returncode, 10, result.stderr)
        self.assertEqual(output["status"], "degraded")
        self.assertEqual(output["warnings"][0]["code"], "start_question_missing")

    def test_network_check_is_opt_in_and_access_failure_has_distinct_exit(self) -> None:
        temp_dir, repo, _ = self.make_configured_project()
        self.addCleanup(temp_dir.cleanup)
        binary_dir, _ = self.make_qmd(Path(temp_dir.name))
        git_log = self.make_git_proxy(Path(temp_dir.name), binary_dir, remote_exit=1)

        result = self.run_cli(repo, "--network", "--json", path_prefix=binary_dir)
        output = json.loads(result.stdout)

        self.assertEqual(result.returncode, 32, result.stderr)
        self.assertEqual(output["status"], "blocked")
        self.assertEqual(output["errors"][0]["code"], "remote_access_denied")
        self.assertTrue(any("ls-remote --exit-code" in line for line in git_log.read_text().splitlines()))
        self.assertFalse(any("fetch" in line for line in git_log.read_text().splitlines()))

    def test_human_output_is_complete_without_color_or_tty(self) -> None:
        temp_dir, repo, _ = self.make_configured_project()
        self.addCleanup(temp_dir.cleanup)
        binary_dir, _ = self.make_qmd(Path(temp_dir.name))

        result = self.run_cli(
            repo,
            "--explain",
            path_prefix=binary_dir,
            extra_env={"NO_COLOR": "1"},
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Memory Doctor", result.stdout)
        self.assertIn("Status: READY", result.stdout)
        self.assertIn("Start question", result.stdout)
        self.assertIn("What should I know before working on this project?", result.stdout)
        self.assertNotIn("\x1b[", result.stdout)
        self.assertNotIn("? [", result.stdout)

    def test_fix_repairs_only_managed_projection_files_and_is_idempotent(self) -> None:
        temp_dir, repo, _ = self.make_configured_project()
        self.addCleanup(temp_dir.cleanup)
        binary_dir, _ = self.make_qmd(Path(temp_dir.name))
        pointer = repo / ".agents" / "project-memory.md"
        pointer.unlink()

        first = self.run_cli(repo, "--fix", "--json", path_prefix=binary_dir)
        first_output = json.loads(first.stdout)
        snapshot = (pointer.read_bytes(), pointer.stat().st_mtime_ns)
        second = self.run_cli(repo, "--fix", "--json", path_prefix=binary_dir)

        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first_output["status"], "ready")
        self.assertTrue(pointer.is_file())
        self.assertEqual((pointer.read_bytes(), pointer.stat().st_mtime_ns), snapshot)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(self.run_git(repo, "status", "--porcelain").stdout, "")

    def test_local_p95_stays_below_two_seconds_for_two_pilot_shapes(self) -> None:
        durations: list[float] = []
        cleanups: list[tempfile.TemporaryDirectory[str]] = []
        self.addCleanup(lambda: [cleanup.cleanup() for cleanup in cleanups])
        for project_id, collection in (
            ("skillz-claude", "elsolal-wiki"),
            ("pleepole-back", "pleepole-wiki"),
        ):
            temp_dir, repo, _ = self.make_configured_project(
                project_id=project_id,
                collection=collection,
            )
            cleanups.append(temp_dir)
            binary_dir, _ = self.make_qmd(
                Path(temp_dir.name),
                collection=collection,
            )
            for _ in range(10):
                started = time.perf_counter()
                result = self.run_cli(repo, "--json", path_prefix=binary_dir)
                durations.append(time.perf_counter() - started)
                self.assertEqual(result.returncode, 0, result.stderr)

        ordered = sorted(durations)
        p95 = ordered[max(0, int(len(ordered) * 0.95) - 1)]
        self.assertLess(p95, 2.0, f"doctor p95 was {p95:.3f}s")


if __name__ == "__main__":
    unittest.main()
