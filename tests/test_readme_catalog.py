import json
from pathlib import Path
import re
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
# Generated adapters of the /wiki-* commands; the README documents the commands themselves.
GENERATED_SKILL_PREFIX = "source-command-"


def catalog_names(artifact_type: str) -> list[str]:
    catalog = json.loads((REPO_ROOT / "core/catalog.yaml").read_text(encoding="utf-8"))
    return sorted(
        item["aliases"]["default"]
        for item in catalog["artifacts"]
        if item["type"] == artifact_type
    )


class ReadmeCatalogTests(unittest.TestCase):
    def setUp(self):
        self.readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    def test_readme_lists_every_catalog_skill(self):
        missing = [
            name
            for name in catalog_names("skill")
            if not name.startswith(GENERATED_SKILL_PREFIX) and f"`{name}`" not in self.readme
        ]
        self.assertEqual(missing, [], "skills missing from README.md")

    def test_readme_lists_every_catalog_command(self):
        missing = [
            name
            for name in catalog_names("command")
            if not re.search(rf"`/{re.escape(name)}(?![\w-])", self.readme)
        ]
        self.assertEqual(missing, [], "commands missing from README.md")


if __name__ == "__main__":
    unittest.main()
