from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]

TASK_FIRST_SURFACES = (
    ".claude/skills/llm-wiki/references/query-workflow.md",
    ".claude/skills/llm-wiki/SKILL.md",
    ".claude/skills/llm-wiki/README.md",
    ".claude/skills/llm-wiki/agents/wiki-librarian.md",
    ".claude/skills/llm-wiki/commands/wiki-query.md",
    ".claude/commands/wiki-query.md",
    ".claude/skills/llm-wiki/assets/CLAUDE.md.template",
    ".claude/skills/llm-wiki/assets/AGENTS.md.template",
    ".claude/skills/llm-wiki/references/cross-tool-setup.md",
    ".claude/skills/llm-wiki/memory_cli/projection.py",
    "scripts/setup-wiki.sh",
    ".claude/CLAUDE.md",
    ".codex/AGENTS.md",
    ".gemini/GEMINI.md",
    ".opencode/AGENTS.md",
    "README.md",
)

LEGACY_ROUTE_SURFACES = tuple(
    path
    for path in TASK_FIRST_SURFACES
    if path != ".claude/skills/llm-wiki/memory_cli/projection.py"
)

FORBIDDEN_INDEX_FIRST = (
    re.compile(r"\bread(?:s|ing)?\s+`?(?:wiki/)?index\.md`?\s+first\b", re.IGNORECASE),
    re.compile(r"\bindex-first\s+read\b", re.IGNORECASE),
    re.compile(r"\blire\s+d['’]abord\s+`?wiki/index\.md`?", re.IGNORECASE),
)


class TaskFirstInstructionContractTests(unittest.TestCase):
    def read(self, relative_path: str) -> str:
        return (REPO_ROOT / relative_path).read_text(encoding="utf-8")

    def test_no_installed_surface_requires_index_first_retrieval(self) -> None:
        for relative_path in TASK_FIRST_SURFACES:
            content = self.read(relative_path)
            with self.subTest(path=relative_path):
                for pattern in FORBIDDEN_INDEX_FIRST:
                    self.assertIsNone(pattern.search(content), pattern.pattern)

    def test_query_contract_exposes_activated_degraded_and_legacy_routes(self) -> None:
        for relative_path in TASK_FIRST_SURFACES:
            content = self.read(relative_path).lower()
            with self.subTest(path=relative_path):
                self.assertIn(".agents/memory.yaml", content)
                self.assertIn("memory context", content)
                self.assertRegex(content, r"entry[_ -]pages")

        for relative_path in LEGACY_ROUTE_SURFACES:
            content = self.read(relative_path).lower()
            with self.subTest(path=relative_path, route="legacy"):
                self.assertIn("non-pilot", content)

    def test_claude_command_copies_remain_identical(self) -> None:
        embedded = self.read(".claude/skills/llm-wiki/commands/wiki-query.md")
        claude = self.read(".claude/commands/wiki-query.md")
        self.assertEqual(embedded, claude)


if __name__ == "__main__":
    unittest.main()
