from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class InstallLifecycleCertificationTests(unittest.TestCase):
    def test_p0_installer_lifecycle_report_is_fresh(self):
        completed = subprocess.run(
            [
                "bash",
                "tests/run-python310.sh",
                "tooling/runtime/certify_install_lifecycle.py",
                "--root",
                ".",
                "--output",
                "docs/compatibility/install-lifecycle-v6.1.json",
                "--check",
            ],
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
