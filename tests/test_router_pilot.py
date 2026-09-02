import json
from pathlib import Path
import subprocess
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT = REPO_ROOT / "docs/compatibility/router-pilot-figma-generate-library.json"


class RouterPilotTests(unittest.TestCase):
    def test_measured_router_report_is_fresh(self):
        result = subprocess.run(
            [
                "bash",
                "tests/run-python310.sh",
                "tooling/evals/router_pilot.py",
                "--root",
                ".",
                "--output",
                REPORT.relative_to(REPO_ROOT).as_posix(),
                "--check",
            ],
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_router_reduces_every_route_without_losing_assertions(self):
        report = json.loads(REPORT.read_text(encoding="utf-8"))
        self.assertTrue(report["decision"]["generalize_router_pattern"])
        self.assertLess(report["router"]["entry_bytes"], report["baseline"]["entry_bytes"])
        for route in report["routes"]:
            self.assertGreater(route["context_reduction_bytes"], 0)
            self.assertEqual(route["assertions_after"], route["assertions_before"])
            self.assertEqual(route["assertion_success_rate"], 1.0)

    def test_catalog_distributes_router_and_all_declared_resources(self):
        catalog = json.loads((REPO_ROOT / "core/catalog.yaml").read_text(encoding="utf-8"))
        artifact = next(
            item for item in catalog["artifacts"] if item["id"] == "figma-generate-library"
        )
        source_root = REPO_ROOT / ".claude/skills/figma-generate-library"
        declared = {item["source"] for item in artifact["resources"]}
        expected = {
            path.relative_to(REPO_ROOT).as_posix()
            for folder in ("references", "scripts")
            for path in (source_root / folder).rglob("*")
            if path.is_file()
        }
        self.assertEqual(declared, expected)
        for provider in artifact["providers"]:
            emitted = REPO_ROOT / "dist" / provider / "skills" / artifact["aliases"]["default"]
            self.assertTrue((emitted / "SKILL.md").is_file())
            for resource in artifact["resources"]:
                self.assertEqual(
                    (emitted / resource["output"]).read_bytes(),
                    (REPO_ROOT / resource["source"]).read_bytes(),
                )


if __name__ == "__main__":
    unittest.main()
