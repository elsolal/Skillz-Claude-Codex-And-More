from __future__ import annotations

import sys
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_ROOT))

from memory_cli.tokens import ESTIMATOR_VERSION, estimate_tokens  # noqa: E402


class TokenEstimatorTests(unittest.TestCase):
    def test_utf8_bytes_div_4_v1_is_exact_and_unicode_aware(self) -> None:
        self.assertEqual(ESTIMATOR_VERSION, "utf8_bytes_div_4_v1")
        self.assertEqual(estimate_tokens(""), 0)
        self.assertEqual(estimate_tokens("abcd"), 1)
        self.assertEqual(estimate_tokens("abcde"), 2)
        self.assertEqual(estimate_tokens("éé"), 1)
        self.assertEqual(estimate_tokens("🙂"), 1)

    def test_estimator_rejects_non_text_values(self) -> None:
        with self.assertRaises(TypeError):
            estimate_tokens(b"not text")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
