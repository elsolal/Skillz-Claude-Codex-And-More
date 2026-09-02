from __future__ import annotations

import unittest
from datetime import date

from memory_cli.conflicts import requires_human, validate_debt_action
from memory_cli.contracts import ConflictCategory, ConflictRisk, DebtAction
from memory_cli.events import EventIntegrityError


class MemoryConflictPolicyTests(unittest.TestCase):
    def test_only_high_product_architecture_security_and_data_require_human(self) -> None:
        blocking = {
            ConflictCategory.PRODUCT,
            ConflictCategory.ARCHITECTURE,
            ConflictCategory.SECURITY,
            ConflictCategory.DATA,
        }

        for category in ConflictCategory:
            for risk in ConflictRisk:
                with self.subTest(category=category, risk=risk):
                    self.assertEqual(
                        requires_human(category=category, risk=risk),
                        risk is ConflictRisk.HIGH and category in blocking,
                    )

    def test_debt_actions_have_closed_metadata_only_arguments(self) -> None:
        self.assertEqual(
            validate_debt_action(
                action=DebtAction.FIX,
                reason=None,
                snooze_until=None,
                today=date(2026, 7, 24),
            ),
            {"action": "fix", "reason": None, "snooze_until": None},
        )
        self.assertEqual(
            validate_debt_action(
                action=DebtAction.IGNORE,
                reason="not_actionable",
                snooze_until=None,
                today=date(2026, 7, 24),
            )["reason"],
            "not_actionable",
        )
        self.assertEqual(
            validate_debt_action(
                action=DebtAction.SNOOZE,
                reason=None,
                snooze_until="2026-08-01",
                today=date(2026, 7, 24),
            )["snooze_until"],
            "2026-08-01",
        )

        invalid = (
            (DebtAction.FIX, "free_text", None),
            (DebtAction.IGNORE, None, None),
            (DebtAction.IGNORE, "contains spaces", None),
            (DebtAction.SNOOZE, None, None),
            (DebtAction.SNOOZE, None, "2026-07-23"),
        )
        for action, reason, snooze_until in invalid:
            with self.subTest(action=action, reason=reason, snooze_until=snooze_until):
                with self.assertRaises(EventIntegrityError):
                    validate_debt_action(
                        action=action,
                        reason=reason,
                        snooze_until=snooze_until,
                        today=date(2026, 7, 24),
                    )


if __name__ == "__main__":
    unittest.main()
