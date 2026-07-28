from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "manifest-v1"
sys.path.insert(0, str(SKILL_ROOT))

from memory_cli.contracts import RepositorySourceKind, TrustLevel  # noqa: E402
from memory_cli.manifest import ManifestError, load_manifest  # noqa: E402
from memory_cli.repository_contracts import select_repository_contracts  # noqa: E402


class RepositoryContractsManifestTests(unittest.TestCase):
    def load_payload(self) -> dict[str, object]:
        return json.loads((FIXTURES / "valid.json").read_text())

    def write_payload(self, root: Path, payload: object) -> Path:
        (root / ".git").mkdir(exist_ok=True)
        (root / ".agents").mkdir(exist_ok=True)
        path = root / ".agents" / "memory.yaml"
        path.write_text(json.dumps(payload))
        return path

    def add_contract_source(self, payload: dict[str, object]) -> None:
        payload["sources"] = [
            {
                "id": "repository-contracts",
                "kind": "qmd",
                "trust": "current_contract",
                "collection": "skillz-contracts",
                "include": [
                    "docs/**/*.md",
                    "openapi/**/*.yaml",
                    "schemas/**/*.json",
                    "database/**/*.sql",
                ],
                "exclude": ["docs/drafts/**"],
            }
        ]

    def test_typed_contract_source_is_optional_and_backward_compatible(self) -> None:
        legacy = load_manifest(FIXTURES / "valid.json")
        self.assertEqual(legacy.sources, ())

        payload = self.load_payload()
        self.add_contract_source(payload)
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest = load_manifest(self.write_payload(Path(temp_dir), payload))

        source = manifest.sources[0]
        self.assertEqual(source.kind, RepositorySourceKind.QMD)
        self.assertEqual(source.trust, TrustLevel.CURRENT_CONTRACT)
        self.assertEqual(source.collection, "skillz-contracts")
        self.assertEqual(source.include[0], "docs/**/*.md")

    def test_contract_source_rejects_unknown_trust_and_non_contract_extensions(self) -> None:
        cases = (
            (("trust", "historical_memory"), "invalid_enum"),
            (("include", ["src/**/*.py"]), "contract_extension_forbidden"),
        )
        for (field, value), expected_code in cases:
            with self.subTest(field=field):
                payload = self.load_payload()
                self.add_contract_source(payload)
                payload["sources"][0][field] = value  # type: ignore[index]
                with tempfile.TemporaryDirectory() as temp_dir:
                    path = self.write_payload(Path(temp_dir), payload)
                    with self.assertRaises(ManifestError) as raised:
                        load_manifest(path)
                self.assertEqual(raised.exception.code, expected_code)


class RepositoryContractsSelectionTests(unittest.TestCase):
    def test_immutable_denylist_and_symlink_boundary_override_broad_glob(self) -> None:
        payload = RepositoryContractsManifestTests().load_payload()
        payload["sources"] = [
            {
                "id": "repository-contracts",
                "kind": "qmd",
                "trust": "current_contract",
                "collection": "skillz-contracts",
                "include": ["**/*"],
                "exclude": [],
            }
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repo"
            root.mkdir()
            manifest_path = RepositoryContractsManifestTests().write_payload(root, payload)
            (root / "docs").mkdir()
            (root / "docs" / "adr.md").write_text("# ADR\n")
            (root / "openapi").mkdir()
            (root / "openapi" / "api.yaml").write_text("openapi: 3.1.0\n")
            (root / "schemas").mkdir()
            (root / "schemas" / "domain.json").write_text("{}\n")
            (root / "database").mkdir()
            (root / "database" / "schema.sql").write_text("create table example();\n")
            (root / ".env").write_text("TOKEN=private\n")
            (root / "logs").mkdir()
            (root / "logs" / "debug.json").write_text("{}\n")
            (root / "dist").mkdir()
            (root / "dist" / "schema.json").write_text("{}\n")
            (root / "src").mkdir()
            (root / "src" / "app.py").write_text("print('app')\n")
            outside = Path(temp_dir) / "outside.md"
            outside.write_text("private\n")
            (root / "docs" / "escape.md").symlink_to(outside)
            (root / "docs" / "alias.json").symlink_to(root / "dist" / "schema.json")

            source = load_manifest(manifest_path).sources[0]
            selection = select_repository_contracts(source, repository_root=root)

        self.assertEqual(
            [path.as_posix() for path in selection.allowed],
            [
                "database/schema.sql",
                "docs/adr.md",
                "openapi/api.yaml",
                "schemas/domain.json",
            ],
        )
        rejected = {item.path.as_posix(): item.code for item in selection.rejected}
        self.assertEqual(rejected[".env"], "immutable_denylist")
        self.assertEqual(rejected["logs"], "immutable_denylist")
        self.assertEqual(rejected["dist"], "immutable_denylist")
        self.assertEqual(rejected["src/app.py"], "contract_extension_forbidden")
        self.assertEqual(rejected["docs/escape.md"], "repository_symlink_escape")
        self.assertEqual(rejected["docs/alias.json"], "repository_symlink_forbidden")


if __name__ == "__main__":
    unittest.main()
