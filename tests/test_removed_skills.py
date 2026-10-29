import json
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
REMOVED_SKILLS = (
    "api-designer",
    "brutalist-skill",
    "code-implementer",
    "code-reviewer",
    "database-designer",
    "elevenlabs",
    "figma-code-connect",
    "figma-create-design-system-rules",
    "figma-create-new-file",
    "figma-generate-design",
    "figma-implement-design",
    "figma-use",
    "github-issue-reader",
    "gpt-tasteskill",
    "images-taste-skill",
    "multi-mind",
    "orchestrate",
    "output-skill",
    "remotion",
    "security-auditor",
    "stitch-skill",
    "test-runner",
)
REMOVED_COMMANDS = (
    "changelog",
    "docs",
    "init",
    "metrics",
    "multi-mind",
    "orchestrate",
    "refactor",
)
COMMAND_DIRECTORIES = ("commands", "prompts")


class RemovedSkillsTests(unittest.TestCase):
    def test_catalog_no_longer_declares_removed_artifacts(self):
        catalog = json.loads((REPO_ROOT / "core/catalog.yaml").read_text(encoding="utf-8"))
        sources = {item["source"] for item in catalog["artifacts"]}
        dependencies = {
            dependency for item in catalog["artifacts"] for dependency in item["dependencies"]
        }
        for name in REMOVED_SKILLS:
            self.assertNotIn(f"core/skills/{name}/SKILL.md", sources)
            self.assertNotIn(name, dependencies)
        for name in REMOVED_COMMANDS:
            self.assertNotIn(f"core/commands/{name}.md", sources)

    def test_removed_artifacts_are_absent_from_sources_and_distributions(self):
        roots = [REPO_ROOT / "core", REPO_ROOT / ".claude"]
        roots += [path for path in (REPO_ROOT / "dist").iterdir() if path.is_dir()]
        leftovers: list[str] = []
        for root in roots:
            for name in REMOVED_SKILLS:
                if (root / "skills" / name).exists():
                    leftovers.append(f"{root.relative_to(REPO_ROOT)}/skills/{name}")
            for directory in COMMAND_DIRECTORIES:
                for name in REMOVED_COMMANDS:
                    leftovers.extend(
                        path.relative_to(REPO_ROOT).as_posix()
                        for path in (root / directory).glob(f"{name}.*")
                    )
        self.assertEqual(leftovers, [])


if __name__ == "__main__":
    unittest.main()
