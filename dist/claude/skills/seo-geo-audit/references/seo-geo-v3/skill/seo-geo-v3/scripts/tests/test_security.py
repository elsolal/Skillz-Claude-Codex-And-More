#!/usr/bin/env python3
"""Security regressions for the Skillz-Claude V3 integration."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1]
ADVANCED = SCRIPTS / "advanced"
for candidate in (SCRIPTS, ADVANCED):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import collect_site  # noqa: E402
import create_project  # noqa: E402
import rule_source_check  # noqa: E402
import validate_project  # noqa: E402


class SecurityRegressionTests(unittest.TestCase):
    def test_authorization_requires_real_actor_and_timestamp(self) -> None:
        self.assertFalse(collect_site._authorization_confirmed({
            "authorized_by": "À renseigner avant collecte",
            "authorized_at": "2026-08-03T12:00:00Z",
        }))
        self.assertFalse(collect_site._authorization_confirmed({
            "authorized_by": "Direction Example",
            "authorized_at": None,
        }))
        self.assertFalse(collect_site._authorization_confirmed({
            "authorized_by": "Direction Example",
            "authorized_at": "2026-08-03T12:00:00",
        }))
        self.assertTrue(collect_site._authorization_confirmed({
            "authorized_by": "Direction Example",
            "authorized_at": "2026-08-03T12:00:00Z",
        }))

    def test_new_project_does_not_claim_authorization(self) -> None:
        kit_root = SCRIPTS.parent / "assets" / "kit"
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "client"
            create_project.create_project(project, "Example", "https://example.com", kit_root=kit_root)
            manifest = json.loads((project / "audit_manifest.json").read_text(encoding="utf-8"))
            self.assertIsNone(manifest["authorization"]["authorized_at"])
            issues = validate_project.validate_project(project, kit_root)
            self.assertEqual(issues, [])

    def test_rule_source_checker_rejects_private_ip_literals(self) -> None:
        with self.assertRaises(ValueError):
            rule_source_check._validate_url("https://127.0.0.1/rules", {"127.0.0.1"})
        with self.assertRaises(ValueError):
            rule_source_check._validate_url("https://[::1]/rules", {"::1"})

    def test_dns_resolution_rejects_private_answers(self) -> None:
        private_answer = [
            (collect_site.socket.AF_INET, collect_site.socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443)),
        ]
        with patch.object(collect_site.socket, "getaddrinfo", return_value=private_answer):
            with self.assertRaises(collect_site.UnsafeURL):
                collect_site._public_endpoints("example.com", 443)


if __name__ == "__main__":
    unittest.main()
