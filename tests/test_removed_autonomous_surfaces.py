from pathlib import Path
import re
import subprocess
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
REMOVED_TOKENS = (
    b"ra" + b"lph",
    b"auto" + b"-loop",
    b"auto" + b"-dev",
    b"auto" + b"-discovery",
    b"cancel" + b"-ra" + b"lph",
    b"resume" + b"-ra" + b"lph",
    b"ra" + b"lph-logs",
    b"ra" + b"lph-state",
)
PROHIBITED = re.compile(
    b"|".join(re.escape(token) for token in REMOVED_TOKENS),
    re.IGNORECASE,
)
ALLOWED_EXACT = {
    "CHANGELOG.md",
    "docs/migrations/v6.1-" + "ra" + "lph-removal.md",
}
ALLOWED_PREFIXES = (
    ".claude/migrations/",
    "docs/compatibility/golden/",
    "docs/planning/",
    "docs/quality/",
)


def tracked_paths() -> list[str]:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPO_ROOT,
        check=True,
        stdout=subprocess.PIPE,
    )
    return sorted(path for path in completed.stdout.decode("utf-8").split("\0") if path)


def is_allowed_history(relative_path: str) -> bool:
    return relative_path in ALLOWED_EXACT or relative_path.startswith(ALLOWED_PREFIXES)


class RemovedAutonomousSurfaceTests(unittest.TestCase):
    def test_no_removed_surface_is_active(self):
        violations: list[str] = []
        for relative_path in tracked_paths():
            if is_allowed_history(relative_path):
                continue
            absolute_path = REPO_ROOT / relative_path
            if not absolute_path.exists() and not absolute_path.is_symlink():
                continue
            if PROHIBITED.search(relative_path.encode("utf-8")):
                violations.append(f"forbidden path: {relative_path}")
                continue
            if absolute_path.is_symlink() or not absolute_path.is_file():
                continue
            content = absolute_path.read_bytes()
            for line_number, line in enumerate(content.splitlines(), start=1):
                if PROHIBITED.search(line):
                    violations.append(f"{relative_path}:{line_number}")

        self.assertEqual(
            violations,
            [],
            "Removed autonomous surfaces remain outside the historical allowlist:\n"
            + "\n".join(violations),
        )


if __name__ == "__main__":
    unittest.main()
