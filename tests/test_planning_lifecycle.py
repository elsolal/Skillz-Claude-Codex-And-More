import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "validate_planning_lifecycle.py"


def load_module():
    spec = importlib.util.spec_from_file_location("planning_lifecycle", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def document(
    document_id: str,
    version: str,
    lifecycle: str = "current",
    superseded_by: str = "null",
    amended_by: str = "[]",
    amends: str = "[]",
) -> str:
    return (
        "---\n"
        f"document_id: {document_id}\n"
        f'version: "{version}"\n'
        f"lifecycle: {lifecycle}\n"
        f"superseded_by: {superseded_by}\n"
        f"amended_by: {amended_by}\n"
        f"amends: {amends}\n"
        "---\n\n# Document\n"
    )


class PlanningLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lifecycle = load_module()

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        self.docs = self.root / "docs" / "planning" / "specs"
        self.docs.mkdir(parents=True)

    def write(self, name: str, content: str) -> Path:
        path = self.docs / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_valid_current_and_superseded_documents(self):
        current = self.write("current.md", document("spec.current", "2"))
        old = self.write(
            "old.md",
            document("spec.old", "1", "superseded", "current.md"),
        )

        report = self.lifecycle.validate(self.root, [current, old])

        self.assertEqual(report["status"], "valid")
        self.assertEqual(report["superseded"], 1)

    def test_duplicate_current_identity_is_rejected(self):
        first = self.write("first.md", document("spec.same", "1"))
        second = self.write("second.md", document("spec.same", "1"))

        report = self.lifecycle.validate(self.root, [first, second])

        self.assertEqual(report["status"], "invalid")
        self.assertTrue(any("duplicate current document" in item for item in report["errors"]))

    def test_missing_superseded_target_is_rejected(self):
        old = self.write(
            "old.md",
            document("spec.old", "1", "superseded", "missing.md"),
        )

        report = self.lifecycle.validate(self.root, [old])

        self.assertTrue(any("target does not exist" in item for item in report["errors"]))

    def test_amendment_links_must_be_bidirectional(self):
        source = self.write(
            "source.md",
            document("spec.source", "1", amended_by='["amendment.md"]'),
        )
        amendment = self.write("amendment.md", document("spec.amendment", "1"))

        invalid = self.lifecycle.validate(self.root, [source, amendment])
        amendment.write_text(
            document("spec.amendment", "1", amends='["source.md"]'),
            encoding="utf-8",
        )
        valid = self.lifecycle.validate(self.root, [source, amendment])

        self.assertTrue(any("incomplete amendment link" in item for item in invalid["errors"]))
        self.assertEqual(valid["status"], "valid")

    def test_missing_schema_and_unsafe_link_are_rejected(self):
        missing = self.write("missing.md", "# No frontmatter\n")
        unsafe = self.write(
            "unsafe.md",
            document("spec.unsafe", "1", "superseded", "../outside.md"),
        )

        report = self.lifecycle.validate(self.root, [missing, unsafe])

        self.assertTrue(any("missing top-level frontmatter" in item for item in report["errors"]))
        self.assertTrue(any("unsafe lifecycle link" in item for item in report["errors"]))

    def test_unquoted_yaml_list_outside_lifecycle_schema_is_tolerated(self):
        path = self.write(
            "existing.md",
            document("spec.existing", "1").replace(
                "---\n\n# Document", "pilots: [Skillz-Claude, Pleepole-back]\n---\n\n# Document"
            ),
        )

        report = self.lifecycle.validate(self.root, [path])

        self.assertEqual(report["status"], "valid")


if __name__ == "__main__":
    unittest.main()
