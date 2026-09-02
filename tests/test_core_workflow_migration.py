import json
from pathlib import Path
import re
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS = (
    "dev-workflow",
    "discovery-workflow",
    "project-probe",
    "quality-gate",
    "ship-workflow",
    "status-workflow",
)
COMMANDS = ("dev", "discovery", "quick-fix", "ship", "status")
RESOURCE_PAIRS = (
    (
        ".claude/knowledge/testing/test-levels-framework.md",
        "core/skills/dev-workflow/references/testing/test-levels-framework.md",
    ),
    (
        ".claude/knowledge/testing/test-priorities-matrix.md",
        "core/skills/dev-workflow/references/testing/test-priorities-matrix.md",
    ),
    (
        ".claude/knowledge/brainstorming/brain-techniques.csv",
        "core/skills/discovery-workflow/references/brainstorming/brain-techniques.csv",
    ),
    (
        ".claude/knowledge/workflows/prd-template.md",
        "core/skills/discovery-workflow/references/workflows/prd-template.md",
    ),
)


def canonicalize_legacy_skill(content: str) -> str:
    content = re.sub(r"\.claude/skills/([a-z0-9-]+)/SKILL\.md", r"skill:\1", content)
    replacements = {
        ".claude/knowledge/testing/test-levels-framework.md":
            "references/testing/test-levels-framework.md",
        ".claude/knowledge/testing/test-priorities-matrix.md":
            "references/testing/test-priorities-matrix.md",
        ".claude/knowledge/brainstorming/brain-techniques.csv":
            "references/brainstorming/brain-techniques.csv",
        ".claude/knowledge/workflows/prd-template.md":
            "references/workflows/prd-template.md",
    }
    for legacy, canonical in replacements.items():
        content = content.replace(legacy, canonical)
    return content


class CoreWorkflowMigrationTests(unittest.TestCase):
    def test_canonical_skills_only_normalize_provider_paths(self):
        for skill in SKILLS:
            legacy = (REPO_ROOT / ".claude" / "skills" / skill / "SKILL.md").read_text(
                encoding="utf-8"
            )
            canonical = (REPO_ROOT / "core" / "skills" / skill / "SKILL.md").read_text(
                encoding="utf-8"
            )
            self.assertEqual(canonical, canonicalize_legacy_skill(legacy), skill)

    def test_canonical_commands_preserve_legacy_bytes(self):
        for command in COMMANDS:
            self.assertEqual(
                (REPO_ROOT / "core" / "commands" / f"{command}.md").read_bytes(),
                (REPO_ROOT / ".claude" / "commands" / f"{command}.md").read_bytes(),
                command,
            )

    def test_canonical_resources_preserve_legacy_bytes(self):
        for legacy, canonical in RESOURCE_PAIRS:
            self.assertEqual(
                (REPO_ROOT / canonical).read_bytes(),
                (REPO_ROOT / legacy).read_bytes(),
                canonical,
            )

    def test_catalog_uses_canonical_workflow_sources(self):
        catalog = json.loads((REPO_ROOT / "core" / "catalog.yaml").read_text(encoding="utf-8"))
        artifacts = {item["id"]: item for item in catalog["artifacts"]}

        for skill in SKILLS:
            self.assertEqual(artifacts[skill]["source"], f"core/skills/{skill}/SKILL.md")
            self.assertEqual(artifacts[skill]["migration_state"], "canonical")
        for command in COMMANDS:
            self.assertEqual(artifacts[command]["source"], f"core/commands/{command}.md")
            self.assertEqual(artifacts[command]["migration_state"], "canonical")

    def test_canonical_workflow_has_no_provider_storage_paths(self):
        forbidden = (".claude/skills/", ".claude/commands/", ".claude/knowledge/")
        paths = [
            *(REPO_ROOT / "core" / "skills").glob("*/SKILL.md"),
            *(REPO_ROOT / "core" / "commands").glob("*.md"),
        ]
        for path in paths:
            content = path.read_text(encoding="utf-8")
            for token in forbidden:
                matches = re.findall(rf"(?<!~/){re.escape(token)}", content)
                self.assertEqual(matches, [], f"{path}: {token}")


if __name__ == "__main__":
    unittest.main()
