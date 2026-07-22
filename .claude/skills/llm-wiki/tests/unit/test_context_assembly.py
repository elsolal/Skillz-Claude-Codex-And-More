from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path, PurePosixPath


SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT))

from memory_cli.assembly import (  # noqa: E402
    DocumentAccessError,
    assemble_context,
    resolve_document,
    section_limit_for,
)
from memory_cli.contracts import (  # noqa: E402
    AssemblyStatus,
    BudgetConfig,
    FreshnessStatus,
    RetrievalHit,
    RetrievalMode,
    RiskReason,
    TaskCategory,
)


def hit(
    path: str,
    *,
    docid: str,
    score: float = 0.90,
    line: int = 1,
    collection: str = "project-wiki",
) -> RetrievalHit:
    return RetrievalHit(
        docid=docid,
        collection=collection,
        relative_path=PurePosixPath(path),
        title=Path(path).stem,
        score=score,
        snippet_line=line,
        snippet="matching text",
    )


class DocumentResolutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name) / "vault"
        (self.root / "wiki" / "entities").mkdir(parents=True)

    def test_resolves_qmd_paths_under_the_projected_wiki_root(self) -> None:
        page = self.root / "wiki" / "entities" / "project.md"
        page.write_text("# Project\n", encoding="utf-8")

        resolved = resolve_document(self.root, PurePosixPath("entities/project.md"))

        self.assertEqual(resolved, page.resolve())

    def test_rejects_traversal_and_symlink_escape_before_reading(self) -> None:
        outside = Path(self.temp_dir.name) / "private.md"
        outside.write_text("private sentinel\n", encoding="utf-8")
        escaped = self.root / "wiki" / "entities" / "escaped.md"
        escaped.symlink_to(outside)

        cases = (
            PurePosixPath("../private.md"),
            PurePosixPath("entities/escaped.md"),
        )
        for relative_path in cases:
            with self.subTest(path=relative_path), self.assertRaises(
                DocumentAccessError
            ) as raised:
                resolve_document(self.root, relative_path)

            self.assertEqual(raised.exception.code, "document_outside_root")
            self.assertNotIn(str(outside), raised.exception.message)


class ContextAssemblyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name) / "vault"
        (self.root / "wiki" / "entities").mkdir(parents=True)
        (self.root / "wiki" / "sources").mkdir(parents=True)

    def write_page(self, relative_path: str, content: str) -> Path:
        page = self.root / "wiki" / relative_path
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(content, encoding="utf-8")
        return page

    def assemble(
        self,
        hits: tuple[RetrievalHit, ...],
        *,
        budget: BudgetConfig = BudgetConfig(target_tokens=800, hard_tokens=1200),
        risk_reason: RiskReason | None = None,
    ):
        return assemble_context(
            hits,
            mode=RetrievalMode.PROJECT,
            task_category=TaskCategory.ARCHITECTURE,
            freshness=FreshnessStatus.FRESH,
            thresholds_version="qmd-0.9-v1",
            budget=budget,
            collection_roots={"project-wiki": self.root},
            risk_reason=risk_reason,
        )

    def test_deduplicates_retrieved_hits_and_emits_markdown_section_metadata(self) -> None:
        content = (
            "---\n"
            "title: Project Memory\n"
            "category: entity\n"
            "summary: Durable project context\n"
            "secret: must-not-be-copied\n"
            "---\n"
            "# Project Memory\n\n"
            "Intro paragraph.\n\n"
            "## Runtime contract\n\n"
            "The codebase remains the immediate source of truth.\n\n"
            "## Later section\n\n"
            "This must not be selected.\n"
        )
        page = self.write_page("entities/project.md", content)
        snippet_line = content.splitlines().index("The codebase remains the immediate source of truth.") + 1

        outcome = self.assemble(
            (
                hit("entities/project.md", docid="#aaaaaa", score=0.80, line=snippet_line),
                hit("entities/project.md", docid="#bbbbbb", score=0.90, line=snippet_line),
            )
        )

        self.assertEqual(outcome.status, AssemblyStatus.READY)
        self.assertEqual([item.docid for item in outcome.retrieved], ["#bbbbbb"])
        self.assertEqual(len(outcome.sections), 1)
        section = outcome.sections[0]
        self.assertEqual(section.relative_path.as_posix(), "entities/project.md")
        self.assertEqual(section.frontmatter["category"], "entity")
        self.assertNotIn("secret", section.frontmatter)
        self.assertIn("## Runtime contract", section.content)
        self.assertNotIn("## Later section", section.content)
        self.assertEqual(section.line_start, snippet_line - 2)
        self.assertLessEqual(section.line_end, len(page.read_text().splitlines()))

    def test_stops_after_sufficient_first_section_without_opening_later_hits(self) -> None:
        first = "# Strong evidence\n\nProject convention.\n"
        self.write_page("entities/strong.md", first)
        outside = Path(self.temp_dir.name) / "outside.md"
        outside.write_text("outside\n", encoding="utf-8")
        (self.root / "wiki" / "entities" / "later.md").symlink_to(outside)

        outcome = self.assemble(
            (
                hit("entities/strong.md", docid="#111111", score=0.91, line=3),
                hit("entities/later.md", docid="#222222", score=0.80, line=1),
            )
        )

        self.assertEqual(outcome.status, AssemblyStatus.READY)
        self.assertEqual(len(outcome.retrieved), 2)
        self.assertEqual([section.docid for section in outcome.sections], ["#111111"])

    def test_truncates_on_a_paragraph_boundary_before_the_target(self) -> None:
        content = (
            "# Budgeted section\n\n"
            "Short essential paragraph.\n\n"
            + "Long optional paragraph " * 80
            + "\n"
        )
        self.write_page("entities/budget.md", content)

        outcome = self.assemble(
            (hit("entities/budget.md", docid="#333333", score=0.91, line=3),),
            budget=BudgetConfig(target_tokens=45, hard_tokens=100),
        )

        self.assertEqual(outcome.status, AssemblyStatus.READY)
        self.assertIn("Short essential paragraph.", outcome.sections[0].content)
        self.assertNotIn("Long optional paragraph", outcome.sections[0].content)
        self.assertTrue(outcome.sections[0].truncated)
        self.assertLessEqual(outcome.estimated_tokens, 45)

    def test_hard_cap_requires_reason_and_exposes_actual_cost_in_both_views(self) -> None:
        content = "# Incident evidence\n\n" + ("critical-data-" * 80) + "\n"
        self.write_page("entities/incident.md", content)
        candidate = (hit("entities/incident.md", docid="#444444", score=0.91, line=3),)
        budget = BudgetConfig(target_tokens=10, hard_tokens=20)

        stopped = self.assemble(candidate, budget=budget)
        allowed = self.assemble(candidate, budget=budget, risk_reason=RiskReason.SECURITY)

        self.assertEqual(stopped.status, AssemblyStatus.PARTIAL)
        self.assertEqual(stopped.sections, ())
        self.assertIn("hard_cap_reached", stopped.reason_codes)
        self.assertEqual(allowed.status, AssemblyStatus.READY)
        self.assertTrue(allowed.hard_cap_exceeded)
        self.assertGreater(allowed.estimated_tokens, budget.hard_tokens)
        self.assertEqual(allowed.receipt_metadata()["risk_reason"], "security")
        self.assertEqual(
            allowed.receipt_metadata()["estimated_tokens"],
            allowed.event_metadata()["estimated_tokens"],
        )
        self.assertEqual(allowed.event_metadata()["risk_reason"], "security")
        self.assertNotIn("content", allowed.event_metadata())

    def test_section_limits_match_the_approved_mode_envelopes(self) -> None:
        self.assertEqual(section_limit_for(RetrievalMode.MINIMAL), 1)
        self.assertEqual(section_limit_for(RetrievalMode.PROJECT), 3)
        self.assertEqual(section_limit_for(RetrievalMode.HISTORICAL), 6)

    def test_all_approved_target_and_hard_budgets_are_preserved(self) -> None:
        self.write_page("entities/strong.md", "# Strong\n\nProject evidence.\n")
        self.write_page("sources/history.md", "# History\n\nHistorical source.\n")
        project_hit = hit("entities/strong.md", docid="#555555", score=0.91, line=3)
        historical_hit = hit("sources/history.md", docid="#666666", score=0.91, line=3)
        cases = (
            (RetrievalMode.MINIMAL, BudgetConfig(800, 1200), (project_hit,)),
            (RetrievalMode.PROJECT, BudgetConfig(2500, 4000), (project_hit,)),
            (
                RetrievalMode.HISTORICAL,
                BudgetConfig(6000, 9000),
                (historical_hit, project_hit),
            ),
        )

        for mode, budget, candidates in cases:
            with self.subTest(mode=mode.value):
                outcome = assemble_context(
                    candidates,
                    mode=mode,
                    task_category=TaskCategory.ARCHITECTURE,
                    freshness=FreshnessStatus.FRESH,
                    thresholds_version="qmd-0.9-v1",
                    budget=budget,
                    collection_roots={"project-wiki": self.root},
                )

                self.assertEqual(outcome.status, AssemblyStatus.READY)
                self.assertEqual(outcome.target_tokens, budget.target_tokens)
                self.assertEqual(outcome.hard_tokens, budget.hard_tokens)


if __name__ == "__main__":
    unittest.main()
