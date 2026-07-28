from __future__ import annotations

import hashlib
import json
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from integration.test_context_cli import ContextCliIntegrationTests


def _tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


class MemoryConflictsCliIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = ContextCliIntegrationTests(
            methodName="test_context_queries_project_first_and_normalizes_hits"
        )
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        (self.fixture.repo / ".claude").mkdir()
        (self.fixture.repo / ".claude" / "project-memory.md").write_text(
            "Repository-first memory contract.\n",
            encoding="utf-8",
        )

    def _context_event_id(self) -> str:
        result = self.fixture._run_cli(
            "--mode",
            "project",
            "--task-category",
            "architecture",
            "--json",
            "memory conflict acceptance",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return str(json.loads(result.stdout)["event_id"])

    def _declare_conflict(
        self,
        *,
        category: str,
        risk: str,
        prepare_debt: bool = True,
    ):
        arguments = [
            "finish",
            self._context_event_id(),
            "--used",
            "#dfec5e",
            "--conflict-docid",
            "#dfec5e",
            "--repo-evidence",
            ".claude/project-memory.md",
            "--evidence-type",
            "contract",
            "--conflict-category",
            category,
            "--conflict-risk",
            risk,
        ]
        if prepare_debt:
            arguments.append("--prepare-debt")
        arguments.append("--json")
        return self.fixture._run_memory_cli(*arguments)

    def test_high_architecture_conflict_returns_21_with_repository_precedence(self) -> None:
        before = _tree_hash(self.fixture.vault)

        result = self._declare_conflict(category="architecture", risk="high")
        output = json.loads(result.stdout)

        self.assertEqual(result.returncode, 21, result.stderr)
        self.assertEqual(output["status"], "conflict")
        self.assertRegex(output["event_id"], r"^con_\d{8}T\d{12}Z_[0-9a-f]{16}$")
        self.assertEqual(
            output["data"]["conflict"],
            {
                "risk": "high",
                "category": "architecture",
                "precedence": "repository",
                "requires_human": True,
                "memory": {
                    "docid": "#dfec5e",
                    "path": "entities/skillz-claude.md",
                    "trust": "durable_memory",
                },
                "repository": {
                    "path": ".claude/project-memory.md",
                    "evidence_type": "contract",
                    "trust": "current_contract",
                },
                "debt": {
                    "id": output["event_id"],
                    "status": "open",
                    "draft": "metadata_only",
                },
                "next_actions": ["continue", "inspect", "prepare_patch"],
            },
        )
        self.assertEqual(_tree_hash(self.fixture.vault), before)

        event_file = next(self.fixture.state_dir.rglob("*.jsonl"))
        events = [json.loads(line) for line in event_file.read_text().splitlines()]
        self.assertEqual(
            [event["event_type"] for event in events],
            ["context_completed", "usage_attested", "memory_conflict"],
        )

    def test_low_conflict_records_open_debt_without_blocking(self) -> None:
        result = self._declare_conflict(category="general", risk="low")
        output = json.loads(result.stdout)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output["status"], "conflict")
        self.assertFalse(output["data"]["conflict"]["requires_human"])
        self.assertEqual(output["data"]["conflict"]["debt"]["status"], "open")

    def test_fix_ignore_and_snooze_are_persisted_without_wiki_mutation(self) -> None:
        before = _tree_hash(self.fixture.vault)
        actions = (
            (["--debt-action", "fix"], {"action": "fix", "reason": None, "snooze_until": None}),
            (
                ["--debt-action", "ignore", "--reason", "not_actionable"],
                {"action": "ignore", "reason": "not_actionable", "snooze_until": None},
            ),
            (
                ["--debt-action", "snooze", "--until", "2099-01-01"],
                {"action": "snooze", "reason": None, "snooze_until": "2099-01-01"},
            ),
        )

        for arguments, expected in actions:
            with self.subTest(action=expected["action"]):
                conflict = self._declare_conflict(category="general", risk="low")
                conflict_id = str(json.loads(conflict.stdout)["event_id"])
                result = self.fixture._run_memory_cli(
                    "finish", conflict_id, *arguments, "--json"
                )
                output = json.loads(result.stdout)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(output["status"], "ready")
                self.assertEqual(output["data"]["debt_action"], expected)
                self.assertEqual(output["data"]["debt_id"], conflict_id)

        self.assertEqual(_tree_hash(self.fixture.vault), before)

    def test_invalid_conflict_or_debt_action_does_not_append(self) -> None:
        parent_id = self._context_event_id()
        invalid_path = self.fixture._run_memory_cli(
            "finish",
            parent_id,
            "--conflict-docid",
            "#dfec5e",
            "--repo-evidence",
            "/Users/private/secret.md",
            "--evidence-type",
            "contract",
            "--conflict-category",
            "architecture",
            "--conflict-risk",
            "high",
            "--json",
        )
        self.assertEqual(invalid_path.returncode, 50, invalid_path.stderr)
        event_file = next(self.fixture.state_dir.rglob("*.jsonl"))
        self.assertEqual(len(event_file.read_text().splitlines()), 1)

        secret_path = (
            self.fixture.repo
            / "evidence"
            / "sk-proj-abcdefghijklmnopqrstuvwxyz1234567890"
        )
        secret_path.parent.mkdir(parents=True, exist_ok=True)
        secret_path.write_text("secret-shaped filename\n", encoding="utf-8")

        for invalid_reference in (
            "user said password hunter2 and this is raw transcript material",
            "docs/not-present.md",
            "sk-proj-abcdefghijklmnopqrstuvwxyz1234567890",
            "evidence/sk-proj-abcdefghijklmnopqrstuvwxyz1234567890",
        ):
            with self.subTest(repository_path=invalid_reference):
                invalid_reference_result = self.fixture._run_memory_cli(
                    "finish",
                    parent_id,
                    "--conflict-docid",
                    "#dfec5e",
                    "--repo-evidence",
                    invalid_reference,
                    "--evidence-type",
                    "contract",
                    "--conflict-category",
                    "architecture",
                    "--conflict-risk",
                    "high",
                    "--json",
                )
                self.assertEqual(
                    invalid_reference_result.returncode,
                    50,
                    invalid_reference_result.stderr,
                )
                self.assertNotIn(
                    invalid_reference,
                    invalid_reference_result.stdout + invalid_reference_result.stderr,
                )
                self.assertEqual(len(event_file.read_text().splitlines()), 1)

        conflict = self._declare_conflict(category="general", risk="low")
        conflict_id = str(json.loads(conflict.stdout)["event_id"])
        lines_before = event_file.read_text().splitlines()
        invalid_action = self.fixture._run_memory_cli(
            "finish",
            conflict_id,
            "--debt-action",
            "ignore",
            "--reason",
            "contains private free text",
            "--json",
        )
        self.assertEqual(invalid_action.returncode, 50, invalid_action.stderr)
        self.assertEqual(event_file.read_text().splitlines(), lines_before)

    def test_concurrent_debt_review_appends_exactly_one_action(self) -> None:
        conflict = self._declare_conflict(category="general", risk="low")
        conflict_id = str(json.loads(conflict.stdout)["event_id"])

        def review(_: int):
            return self.fixture._run_memory_cli(
                "finish",
                conflict_id,
                "--debt-action",
                "fix",
                "--json",
            )

        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(review, range(8)))

        self.assertEqual(sum(result.returncode == 0 for result in results), 1)
        self.assertTrue(all(result.returncode in {0, 50} for result in results))
        event_file = next(self.fixture.state_dir.rglob("*.jsonl"))
        events = [json.loads(line) for line in event_file.read_text().splitlines()]
        self.assertEqual(
            [event["event_type"] for event in events].count("memory_debt_action"),
            1,
        )


if __name__ == "__main__":
    unittest.main()
