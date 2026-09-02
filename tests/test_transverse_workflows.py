import importlib.util
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_lifecycle_module():
    path = REPO_ROOT / "scripts" / "validate_planning_lifecycle.py"
    spec = importlib.util.spec_from_file_location("planning_lifecycle_transverse", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TransverseWorkflowTests(unittest.TestCase):
    def test_verification_workflows_use_skill_owned_tools(self):
        skills = {
            name: (REPO_ROOT / "core" / "skills" / name / "SKILL.md").read_text(
                encoding="utf-8"
            )
            for name in ("project-probe", "quality-gate", "ship-workflow", "status-workflow")
        }

        self.assertIn("skill:project-probe/scripts/project_probe.py", skills["project-probe"])
        self.assertIn("skill:quality-gate/scripts/gate_verify.py", skills["quality-gate"])
        for text in skills.values():
            self.assertNotIn("bash scripts/run-python310.sh scripts/", text)

        ship = skills["ship-workflow"]
        self.assertNotIn("git diff main...HEAD", ship)
        self.assertNotIn("git fetch origin main", ship)
        self.assertNotIn("If on `main` or `master`", ship)
        self.assertNotIn("non-main branch", skills["status-workflow"])
        self.assertNotIn("`main`, or `master`", skills["quality-gate"])
        self.assertIn("ready-to-ship-with-waiver", skills["status-workflow"])
        self.assertIn("tooling-unavailable", skills["status-workflow"])

    def test_status_defines_every_evidence_backed_state(self):
        canonical = (REPO_ROOT / "core/skills/status-workflow/SKILL.md").read_text(
            encoding="utf-8"
        )
        legacy = (REPO_ROOT / ".claude/skills/status-workflow/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertEqual(canonical, legacy)
        for state in (
            "not-installed",
            "partially-installed",
            "project-unprobed",
            "plan-awaiting-approval",
            "implementation-in-progress",
            "gate-stale",
            "ready-to-ship",
        ):
            self.assertIn(f"`{state}`", canonical)
        for proof in (
            "tooling/install/skillz.py --json doctor",
            "scripts/project_probe.py",
            "scripts/validate_planning_lifecycle.py",
            "scripts/gate_verify.py",
            "providers/*/capabilities.yaml",
        ):
            self.assertIn(proof, canonical)
        self.assertIn("Missing proof means `unknown`", canonical)
        self.assertIn("must not execute the action", canonical)

    def test_retro_has_stable_rework_questions_and_no_automatic_mutation(self):
        retro = (REPO_ROOT / ".claude/commands/retro.md").read_text(encoding="utf-8")
        for question in (
            "Quel délai ou détour aurait pu être évité ?",
            "Quel rework a été provoqué par une hypothèse ou une preuve insuffisante ?",
            "Quel contexte manquait au moment de décider ?",
            "Quelle étape doit être supprimée, simplifiée ou automatisée la prochaine fois ?",
        ):
            self.assertEqual(retro.count(question), 1)
        self.assertIn("observational and read-only", retro)
        self.assertIn("must never update", retro)
        self.assertNotIn("git fetch", retro)
        self.assertNotIn("mkdir -p .context/retros", retro)
        self.assertNotIn("Save Snapshot", retro)

    def test_repository_planning_lifecycle_is_valid(self):
        lifecycle = load_lifecycle_module()
        paths = [
            path
            for directory in lifecycle.DEFAULT_DIRECTORIES
            for path in (REPO_ROOT / "docs/planning" / directory).glob("*.md")
        ]

        report = lifecycle.validate(REPO_ROOT, paths)

        self.assertEqual(report["status"], "valid", report["errors"])
        self.assertEqual(report["documents"], len(paths))
        self.assertGreater(report["current"], 0)
        self.assertGreater(report["superseded"], 0)


if __name__ == "__main__":
    unittest.main()
