import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "project_probe.py"
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "project-probe"


def load_probe_module():
    spec = importlib.util.spec_from_file_location("project_probe", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ProjectProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.probe = load_probe_module()

    def copy_fixture(self, name: str) -> Path:
        fixture_dir = Path(tempfile.mkdtemp()) / name
        shutil.copytree(FIXTURES / name, fixture_dir)
        self.addCleanup(shutil.rmtree, fixture_dir.parent)
        return fixture_dir

    def test_node_fixture_records_commands_and_sources(self):
        result = self.probe.probe_project(FIXTURES / "node")

        self.assertEqual(result["stack"], "node-js")
        self.assertEqual(
            result["commands"],
            {"build": "npm run build", "lint": "npm run lint", "test": "npm test"},
        )
        self.assertEqual(result["command_sources"]["lint"], "package.json#scripts.lint")
        self.assertNotIn("deploy", result["commands"])
        self.assertEqual(result["testability"]["harness"], "vitest")

    def test_python_fixture_detects_required_runtime(self):
        result = self.probe.probe_project(FIXTURES / "python")

        self.assertEqual(result["stack"], "python")
        self.assertEqual(result["python"]["required"], ">=3.11")
        self.assertEqual(result["commands"]["lint"], "python -m ruff check .")
        self.assertEqual(result["commands"]["test"], "python -m pytest")
        self.assertEqual(result["command_sources"]["test"], "pyproject.toml#tool.pytest")

    def test_shell_fixture_uses_allowlist_and_rejects_deploy(self):
        result = self.probe.probe_project(FIXTURES / "shell")

        self.assertEqual(result["stack"], "shell")
        self.assertEqual(result["commands"]["lint"], "bash scripts/lint.sh")
        self.assertEqual(result["commands"]["test"], "bash scripts/test.sh")
        self.assertNotIn("deploy", result["commands"])
        self.assertNotIn("scripts/deploy.sh", result["command_sources"].values())

    def test_monorepo_and_mixed_stacks_are_explicit(self):
        monorepo = self.probe.probe_project(FIXTURES / "monorepo")
        mixed = self.probe.probe_project(FIXTURES / "mixed")

        self.assertEqual(monorepo["stack"], "node-js")
        self.assertEqual(monorepo["monorepo"]["manager"], "pnpm")
        self.assertEqual(monorepo["monorepo"]["workspaces"], ["packages/*"])
        self.assertEqual(mixed["stack"], "mixed")

    def test_fingerprint_hashes_paths_and_contents_deterministically(self):
        fixture = self.copy_fixture("node")
        skill = fixture / ".claude" / "skills" / "critical" / "SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("# One\n", encoding="utf-8")

        first = self.probe.compute_fingerprint(fixture)
        second = self.probe.compute_fingerprint(fixture)
        skill.write_text("# Two\n", encoding="utf-8")
        changed_content = self.probe.compute_fingerprint(fixture)
        renamed = skill.with_name("REFERENCE.md")
        skill.rename(renamed)
        changed_path = self.probe.compute_fingerprint(fixture)

        self.assertEqual(first, second)
        self.assertNotEqual(first["sha256"], changed_content["sha256"])
        self.assertNotEqual(changed_content["sha256"], changed_path["sha256"])
        self.assertIn(".claude/skills/critical/SKILL.md", first["sources"])

    def test_fingerprint_includes_behavioral_cases_tests_and_goldens(self):
        fixture = self.copy_fixture("node")
        files = {
            "behavioral/cases/probe.yaml": "{}\n",
            "behavioral/fixtures/node/index.js": "export {};\n",
            "tests/test_behavior.py": "# test\n",
            "docs/compatibility/golden/provider.json": "{}\n",
        }
        for relative, content in files.items():
            path = fixture / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

        fingerprint = self.probe.compute_fingerprint(fixture)

        for relative in files:
            self.assertIn(relative, fingerprint["sources"])

    def test_git_index_excludes_untracked_provider_state(self):
        fixture = self.copy_fixture("node")
        subprocess.run(["git", "init", "-q"], cwd=fixture, check=True)
        subprocess.run(["git", "add", "package.json", "package-lock.json"], cwd=fixture, check=True)
        user_hook = fixture / ".codex" / "hooks.json"
        user_hook.parent.mkdir()
        user_hook.write_text('{"user_owned": true}\n', encoding="utf-8")

        fingerprint = self.probe.compute_fingerprint(fixture)

        self.assertNotIn(".codex/hooks.json", fingerprint["sources"])
        self.assertIn("package.json", fingerprint["sources"])

    def test_manifest_has_versioned_generator_provenance_and_absence_reasons(self):
        result = self.probe.probe_project(FIXTURES / "shell")
        rendered = self.probe.render_manifest(result)

        self.assertEqual(result["fingerprint_schema_version"], 2)
        self.assertRegex(result["generated_by"], r"^project-probe/[0-9]+\.[0-9]+\.[0-9]+$")
        self.assertIn("selected_interpreter", result["python"])
        self.assertIn("absence_reasons:", rendered)
        self.assertIn("command_sources:", rendered)

    def test_python_39_fails_with_precise_message(self):
        with self.assertRaisesRegex(RuntimeError, "Python 3.10 or newer is required; detected 3.9"):
            self.probe.require_supported_python((3, 9, 18))

    def test_freshness_rejects_legacy_schema_and_generator(self):
        result = self.probe.probe_project(FIXTURES / "shell")
        fixture_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, fixture_dir)
        manifest = fixture_dir / "verification.yaml"
        rendered = self.probe.render_manifest(result)
        manifest.write_text(rendered, encoding="utf-8")

        self.assertTrue(self.probe.manifest_is_fresh(manifest, result))
        manifest.write_text(
            rendered.replace("fingerprint_schema_version: 2", "fingerprint_schema_version: 1"),
            encoding="utf-8",
        )
        self.assertFalse(self.probe.manifest_is_fresh(manifest, result))
        manifest.write_text(
            rendered.replace("project-probe/2.0.0", "project-probe/1.0.0"),
            encoding="utf-8",
        )
        self.assertFalse(self.probe.manifest_is_fresh(manifest, result))

    def test_suspicious_shell_content_is_not_safe_to_probe(self):
        self.assertFalse(self.probe.is_safe_shell_candidate("rm -rf build"))
        self.assertFalse(self.probe.is_safe_shell_candidate("curl https://example.invalid"))
        self.assertTrue(self.probe.is_safe_shell_candidate("bash -n scripts/*.sh"))

    def test_explicit_override_is_provenanced_and_unsafe_command_is_rejected(self):
        fixture = self.copy_fixture("shell")
        config = fixture / ".agents" / "project-probe.json"
        config.parent.mkdir()
        config.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "commands": {
                        "lint": "bash -n scripts/*.sh",
                        "test": "curl https://example.invalid",
                    },
                }
            ),
            encoding="utf-8",
        )

        result = self.probe.probe_project(fixture)

        self.assertEqual(result["commands"]["lint"], "bash -n scripts/*.sh")
        self.assertEqual(
            result["command_sources"]["lint"],
            ".agents/project-probe.json#commands.lint",
        )
        self.assertEqual(result["commands"]["test"], "bash scripts/test.sh")

    def test_shell_lint_checks_files_individually(self):
        fixture = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, fixture)
        scripts = fixture / "scripts"
        scripts.mkdir()
        (scripts / "good.sh").write_text("#!/usr/bin/env bash\nprintf 'ok\\n'\n", encoding="utf-8")
        (scripts / "bad.sh").write_text("#!/usr/bin/env bash\nif then\n", encoding="utf-8")

        completed = subprocess.run(
            ["bash", str(REPO_ROOT / "scripts" / "lint-shell.sh"), str(fixture)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("scripts/bad.sh", completed.stderr)

    def test_python_launcher_reports_incompatible_runtime(self):
        fixture = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, fixture)
        fake_python = fixture / "python3"
        fake_python.write_text(
            "#!/bin/sh\n"
            "if [ \"${1:-}\" = \"--version\" ]; then echo 'Python 3.9.18'; fi\n"
            "exit 1\n",
            encoding="utf-8",
        )
        fake_python.chmod(0o755)

        completed = subprocess.run(
            ["/bin/bash", str(REPO_ROOT / "scripts" / "run-python310.sh"), "-c", "pass"],
            env={"PATH": str(fixture)},
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("Python 3.10 or newer is required", completed.stderr)
        self.assertIn("Python 3.9.18", completed.stderr)


if __name__ == "__main__":
    unittest.main()
