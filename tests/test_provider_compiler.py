import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import tomllib
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "tooling" / "build" / "compiler.py"


def load_compiler():
    spec = importlib.util.spec_from_file_location("provider_compiler", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ProviderCompilerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compiler = load_compiler()

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temp_dir)
        self.fixture = self.temp_dir / "repo"
        shutil.copytree(REPO_ROOT / "core", self.fixture / "core")
        shutil.copytree(REPO_ROOT / "providers", self.fixture / "providers")
        catalog = json.loads((self.fixture / "core" / "catalog.yaml").read_text())
        required = {
            relative
            for artifact in catalog["artifacts"]
            for relative in (
                artifact["source"],
                *(resource["source"] for resource in artifact.get("resources", [])),
            )
        }
        required.add(".claude/commands/quick-fix.md")
        for relative in sorted(required):
            source = REPO_ROOT / relative
            target = self.fixture / relative
            if target.exists():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

    def _catalog(self) -> dict:
        return json.loads((self.fixture / "core" / "catalog.yaml").read_text(encoding="utf-8"))

    def _write_catalog(self, payload: dict) -> None:
        (self.fixture / "core" / "catalog.yaml").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def test_two_builds_are_byte_identical(self):
        first = self.temp_dir / "first"
        second = self.temp_dir / "second"

        first_report = self.compiler.build_repository(self.fixture, first)
        second_report = self.compiler.build_repository(self.fixture, second)

        self.assertEqual(first_report["tree_hash"], second_report["tree_hash"])
        self.assertEqual(self.compiler.compare_trees(first, second), [])

    def test_report_records_supported_pending_and_unsupported(self):
        report = self.compiler.build_repository(self.fixture, self.temp_dir / "dist")
        statuses = {(item["provider"], item["artifact_id"]): item["status"] for item in report["artifacts"]}

        self.assertEqual(
            report["distribution"],
            {"name": "skillz-claude", "version": "6.1.0-dev.1"},
        )
        self.assertEqual(statuses[("claude", "quick-fix")], "supported")
        self.assertEqual(statuses[("agents-generic", "quick-fix")], "unsupported")
        self.assertTrue(any(item["status"] == "pending" for item in report["capabilities"]))

    def test_codex_native_package_is_generated_from_catalog(self):
        output = self.temp_dir / "dist"
        report = self.compiler.build_repository(self.fixture, output)

        manifest = json.loads(
            (output / "codex" / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        marketplace = json.loads(
            (output / "codex" / ".agents" / "plugins" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(manifest["name"], "skillz-claude")
        self.assertEqual(manifest["version"], "6.1.0-dev.1")
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertEqual(marketplace["plugins"][0]["name"], manifest["name"])
        self.assertEqual(marketplace["plugins"][0]["source"], {"source": "local", "path": "./"})
        codex_package = next(item for item in report["packages"] if item["provider"] == "codex")
        self.assertEqual(codex_package["status"], "supported")
        self.assertEqual(codex_package["manifest"], "codex/.codex-plugin/plugin.json")

    def test_native_package_status_does_not_invent_provider_support(self):
        output = self.temp_dir / "dist"
        report = self.compiler.build_repository(self.fixture, output)

        packages = {item["provider"]: item for item in report["packages"]}
        self.assertEqual(packages["claude"]["status"], "supported")
        self.assertEqual(packages["grok"]["status"], "supported")
        self.assertEqual(packages["gemini"]["status"], "supported")
        self.assertEqual(packages["kimi"]["status"], "unsupported")
        self.assertEqual(packages["opencode"]["status"], "unsupported")
        self.assertEqual(packages["agents-generic"]["status"], "unsupported")
        self.assertFalse((output / "opencode" / ".codex-plugin").exists())
        self.assertFalse((output / "agents-generic" / ".codex-plugin").exists())

    def test_kimi_adapter_generates_skills_without_claiming_a_package(self):
        output = self.temp_dir / "dist"
        report = self.compiler.build_repository(self.fixture, output)

        self.assertEqual(
            (output / "kimi" / "skills" / "dev-workflow" / "SKILL.md").read_bytes(),
            (self.fixture / "core" / "skills" / "dev-workflow" / "SKILL.md").read_bytes(),
        )
        self.assertFalse((output / "kimi" / "commands").exists())
        quick_fix = next(
            item
            for item in report["artifacts"]
            if item["provider"] == "kimi" and item["artifact_id"] == "quick-fix"
        )
        self.assertEqual(quick_fix["status"], "unsupported")

    def test_grok_adapter_generates_claude_compatible_plugin(self):
        output = self.temp_dir / "dist"
        report = self.compiler.build_repository(self.fixture, output)

        manifest = json.loads(
            (output / "grok" / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertEqual(manifest["commands"], "./commands/")
        self.assertTrue((output / "grok" / "commands" / "quick-fix.md").is_file())
        package = next(item for item in report["packages"] if item["provider"] == "grok")
        self.assertEqual(package["manifest_format"], "distribution")

    def test_gemini_adapter_generates_extension_and_toml_command(self):
        output = self.temp_dir / "dist"
        report = self.compiler.build_repository(self.fixture, output)

        manifest = json.loads(
            (output / "gemini" / "gemini-extension.json").read_text(encoding="utf-8")
        )
        command = tomllib.loads(
            (output / "gemini" / "commands" / "quick-fix.toml").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["contextFileName"], "GEMINI.md")
        self.assertEqual(manifest["version"], "6.1.0-dev.1")
        self.assertEqual(
            (output / "gemini" / "GEMINI.md").read_bytes(),
            (self.fixture / "providers" / "gemini" / "GEMINI.md").read_bytes(),
        )
        self.assertIn("# Quick Fix", command["prompt"])
        self.assertIn("{{args}}", command["prompt"])
        self.assertNotIn("$ARGUMENTS", command["prompt"])
        self.assertTrue(command["description"].endswith('"description du problème"'))
        package = next(item for item in report["packages"] if item["provider"] == "gemini")
        self.assertEqual(package["manifest_format"], "gemini-extension")

    def test_provider_certification_does_not_exceed_observed_runtime(self):
        for provider, expected_state in (
            ("kimi", "broken"),
            ("grok", "not-installed"),
            ("gemini", "not-installed"),
        ):
            capabilities = json.loads(
                (self.fixture / "providers" / provider / "capabilities.yaml").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(capabilities["certification"], "C1")
            self.assertEqual(capabilities["runtime"]["state_observed"], expected_state)
            self.assertIsNone(capabilities["runtime"]["version_observed"])

    def test_transform_cannot_be_used_for_wrong_artifact_type(self):
        contract_path = self.fixture / "providers" / "gemini" / "build-contract.json"
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        contract["artifacts"]["skill"]["transform"] = "gemini-command"
        contract_path.write_text(json.dumps(contract), encoding="utf-8")

        with self.assertRaisesRegex(self.compiler.BuildError, "supported capability is not implemented"):
            self.compiler.build_repository(self.fixture, self.temp_dir / "dist")

    def test_native_discovery_certification_requires_a_pinned_version(self):
        capabilities_path = self.fixture / "providers" / "gemini" / "capabilities.yaml"
        capabilities = json.loads(capabilities_path.read_text(encoding="utf-8"))
        capabilities["certification"] = "C2"
        capabilities_path.write_text(json.dumps(capabilities), encoding="utf-8")

        with self.assertRaisesRegex(self.compiler.BuildError, "certification lacks a pinned version"):
            self.compiler.build_repository(self.fixture, self.temp_dir / "dist")

    def test_gemini_manifest_cannot_reference_an_absent_context_file(self):
        catalog = self._catalog()
        instructions = next(
            item for item in catalog["artifacts"] if item["id"] == "gemini-instructions"
        )
        instructions["providers"] = []
        self._write_catalog(catalog)

        with self.assertRaisesRegex(self.compiler.BuildError, "context is not generated"):
            self.compiler.build_repository(self.fixture, self.temp_dir / "dist")

    def test_skill_resources_are_copied_and_reported_for_each_supported_provider(self):
        resource = self.fixture / "knowledge" / "testing" / "checklist.md"
        resource.parent.mkdir(parents=True)
        resource.write_text("# Checklist\n", encoding="utf-8")
        catalog = self._catalog()
        dev = next(item for item in catalog["artifacts"] if item["id"] == "dev-workflow")
        dev["resources"] = [
            {
                "source": "knowledge/testing/checklist.md",
                "output": "references/testing/checklist.md",
            }
        ]
        self._write_catalog(catalog)

        output = self.temp_dir / "dist"
        report = self.compiler.build_repository(self.fixture, output)

        for provider in ("agents-generic", "claude", "codex", "gemini", "grok", "kimi", "opencode"):
            generated = (
                output
                / provider
                / "skills"
                / "dev-workflow"
                / "references"
                / "testing"
                / "checklist.md"
            )
            self.assertEqual(generated.read_text(encoding="utf-8"), "# Checklist\n")
        codex_dev = next(
            item
            for item in report["artifacts"]
            if item["provider"] == "codex" and item["artifact_id"] == "dev-workflow"
        )
        self.assertEqual(
            codex_dev["resources"][0]["output"],
            "codex/skills/dev-workflow/references/testing/checklist.md",
        )

    def test_command_can_declare_namespaced_resources(self):
        catalog = self._catalog()
        quick_fix = next(item for item in catalog["artifacts"] if item["id"] == "quick-fix")
        quick_fix["resources"] = [
            {
                "source": ".claude/commands/quick-fix.md",
                "output": "resources/quick-fix/reference.md",
            }
        ]
        self._write_catalog(catalog)
        report = self.compiler.build_repository(self.fixture, self.temp_dir / "dist")
        item = next(
            artifact
            for artifact in report["artifacts"]
            if artifact["provider"] == "claude" and artifact["artifact_id"] == "quick-fix"
        )
        self.assertEqual(
            item["resources"][0]["output"],
            "claude/commands/resources/quick-fix/reference.md",
        )

    def test_resource_path_traversal_is_rejected(self):
        catalog = self._catalog()
        dev = next(item for item in catalog["artifacts"] if item["id"] == "dev-workflow")
        dev["resources"] = [
            {"source": ".claude/commands/quick-fix.md", "output": "../escape.md"}
        ]
        self._write_catalog(catalog)

        with self.assertRaisesRegex(self.compiler.BuildError, "unsafe artifact resource output"):
            self.compiler.build_repository(self.fixture, self.temp_dir / "dist")

    def test_resource_cannot_replace_skill_entrypoint(self):
        catalog = self._catalog()
        dev = next(item for item in catalog["artifacts"] if item["id"] == "dev-workflow")
        dev["resources"] = [
            {"source": ".claude/commands/quick-fix.md", "output": "SKILL.md"}
        ]
        self._write_catalog(catalog)

        with self.assertRaisesRegex(self.compiler.BuildError, "resource replaces SKILL.md"):
            self.compiler.build_repository(self.fixture, self.temp_dir / "dist")

    def test_core_workflow_slice_matches_canonical_sources_across_p0(self):
        output = self.temp_dir / "dist"
        self.compiler.build_repository(self.fixture, output)

        skills = (
            "dev-workflow",
            "discovery-workflow",
            "project-probe",
            "quality-gate",
            "ship-workflow",
            "status-workflow",
        )
        for provider in ("claude", "codex", "opencode"):
            for skill in skills:
                self.assertEqual(
                    (output / provider / "skills" / skill / "SKILL.md").read_bytes(),
                    (self.fixture / "core" / "skills" / skill / "SKILL.md").read_bytes(),
                )
        for provider, directory in (
            ("claude", "commands"),
            ("codex", "prompts"),
            ("opencode", "commands"),
        ):
            for command in ("dev", "discovery", "quick-fix", "ship", "status"):
                self.assertEqual(
                    (output / provider / directory / f"{command}.md").read_bytes(),
                    (self.fixture / "core" / "commands" / f"{command}.md").read_bytes(),
                )

    def test_alias_collision_blocks_build(self):
        catalog = self._catalog()
        quality = next(item for item in catalog["artifacts"] if item["id"] == "quality-gate")
        quality["aliases"]["claude"] = "project-probe"
        self._write_catalog(catalog)

        with self.assertRaisesRegex(self.compiler.BuildError, "alias collision"):
            self.compiler.build_repository(self.fixture, self.temp_dir / "dist")

    def test_missing_dependency_blocks_build(self):
        catalog = self._catalog()
        catalog["artifacts"][0]["dependencies"].append("missing-artifact")
        self._write_catalog(catalog)

        with self.assertRaisesRegex(self.compiler.BuildError, "missing dependency"):
            self.compiler.build_repository(self.fixture, self.temp_dir / "dist")

    def test_capability_claim_without_implementation_blocks_build(self):
        capabilities_path = self.fixture / "providers" / "agents-generic" / "capabilities.yaml"
        capabilities = json.loads(capabilities_path.read_text(encoding="utf-8"))
        capabilities["capabilities"]["command"] = "supported"
        capabilities_path.write_text(json.dumps(capabilities), encoding="utf-8")

        with self.assertRaisesRegex(self.compiler.BuildError, "capability/build mismatch"):
            self.compiler.build_repository(self.fixture, self.temp_dir / "dist")

    def test_package_claim_without_implementation_blocks_build(self):
        capabilities_path = self.fixture / "providers" / "opencode" / "capabilities.yaml"
        capabilities = json.loads(capabilities_path.read_text(encoding="utf-8"))
        capabilities["package"] = "supported"
        capabilities_path.write_text(json.dumps(capabilities), encoding="utf-8")

        with self.assertRaisesRegex(self.compiler.BuildError, "package capability/build mismatch"):
            self.compiler.build_repository(self.fixture, self.temp_dir / "dist")

    def test_unsafe_package_manifest_path_blocks_build(self):
        contract_path = self.fixture / "providers" / "codex" / "build-contract.json"
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        contract["package"]["manifest_path"] = "../plugin.json"
        contract_path.write_text(json.dumps(contract), encoding="utf-8")

        with self.assertRaisesRegex(self.compiler.BuildError, "unsafe provider package manifest"):
            self.compiler.build_repository(self.fixture, self.temp_dir / "dist")

    def test_package_components_cannot_override_catalog_identity(self):
        contract_path = self.fixture / "providers" / "codex" / "build-contract.json"
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        contract["package"]["components"]["name"] = "./spoofed-name"
        contract_path.write_text(json.dumps(contract), encoding="utf-8")

        with self.assertRaisesRegex(self.compiler.BuildError, "unknown package components"):
            self.compiler.build_repository(self.fixture, self.temp_dir / "dist")

    def test_unknown_catalog_provider_blocks_build(self):
        catalog = self._catalog()
        catalog["artifacts"][0]["providers"].append("typo-provider")
        self._write_catalog(catalog)

        with self.assertRaisesRegex(self.compiler.BuildError, "unknown providers"):
            self.compiler.build_repository(self.fixture, self.temp_dir / "dist")

    def test_new_provider_is_discovered_without_compiler_change(self):
        fixture_provider = self.fixture / "providers" / "fixture"
        shutil.copytree(self.fixture / "providers" / "claude", fixture_provider)
        for name in ("capabilities.yaml", "build-contract.json"):
            path = fixture_provider / name
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["provider"] = "fixture"
            if name == "build-contract.json":
                payload["output_root"] = "fixture"
            path.write_text(json.dumps(payload), encoding="utf-8")
        catalog = self._catalog()
        for artifact in catalog["artifacts"]:
            artifact["providers"].append("fixture")
        self._write_catalog(catalog)

        report = self.compiler.build_repository(self.fixture, self.temp_dir / "dist")

        self.assertIn("fixture", report["providers"])

    def test_check_reports_modified_and_orphan_outputs(self):
        output = self.temp_dir / "dist"
        self.compiler.build_repository(self.fixture, output)
        generated = next(path for path in output.rglob("SKILL.md"))
        generated.write_text("manual edit\n", encoding="utf-8")
        (output / "orphan.txt").write_text("orphan\n", encoding="utf-8")

        differences = self.compiler.check_repository(self.fixture, output)

        self.assertTrue(any("orphan.txt" in difference for difference in differences))
        self.assertTrue(any("SKILL.md" in difference for difference in differences))

    def test_invalid_output_template_is_actionable(self):
        contract_path = self.fixture / "providers" / "claude" / "build-contract.json"
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        contract["artifacts"]["skill"]["output_template"] = "skills/{unknown}/SKILL.md"
        contract_path.write_text(json.dumps(contract), encoding="utf-8")

        with self.assertRaisesRegex(
            self.compiler.BuildError,
            "invalid output template for claude/skill",
        ):
            self.compiler.build_repository(self.fixture, self.temp_dir / "dist")

    def test_check_reports_mode_drift(self):
        output = self.temp_dir / "dist"
        self.compiler.build_repository(self.fixture, output)
        generated = next(path for path in output.rglob("SKILL.md"))
        generated.chmod(0o755)

        differences = self.compiler.check_repository(self.fixture, output)

        self.assertTrue(any("modified output" in difference for difference in differences))
        self.assertTrue(any("SKILL.md" in difference for difference in differences))


if __name__ == "__main__":
    unittest.main()
