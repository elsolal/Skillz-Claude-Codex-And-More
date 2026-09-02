from pathlib import Path
import re
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SUPABASE_SKILL = REPO_ROOT / ".claude" / "skills" / "supabase-security" / "SKILL.md"
MUTATING_CURL = re.compile(
    r"curl\s+(?:[^\n]*\s)?(?:-X|--request)\s*(?:POST|PUT|PATCH|DELETE)\b",
    re.IGNORECASE,
)


class ReadOnlySkillContractTests(unittest.TestCase):
    def test_supabase_audit_has_no_mutating_http_example(self):
        content = SUPABASE_SKILL.read_text(encoding="utf-8")

        self.assertIn("strictement read-only", content)
        self.assertIsNone(MUTATING_CURL.search(content))


if __name__ == "__main__":
    unittest.main()
