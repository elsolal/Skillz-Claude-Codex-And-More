import importlib.util
from pathlib import Path
import sys
import tempfile
import time
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from managed_sections import (  # noqa: E402
    ManagedSectionError,
    parse_managed_section,
    prepare_managed_update,
    render_managed_section,
)


def load_update_index():
    path = SCRIPTS / "update_index.py"
    spec = importlib.util.spec_from_file_location("managed_update_index", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ManagedSectionTests(unittest.TestCase):
    def test_round_trip_preserves_unmanaged_prefix_and_suffix(self):
        existing = "Human preface\n" + render_managed_section("index", "old\n") + "Human notes\n"

        candidate, changed = prepare_managed_update(existing, "index", "new\n")

        self.assertTrue(changed)
        self.assertTrue(candidate.startswith("Human preface\n"))
        self.assertTrue(candidate.endswith("Human notes\n"))
        self.assertEqual(parse_managed_section(candidate, "index").body, "new\n")

    def test_missing_or_modified_markers_are_blocked(self):
        with self.assertRaisesRegex(ManagedSectionError, "marker pair"):
            prepare_managed_update("# Legacy index\n", "index", "new\n")
        marked = render_managed_section("index", "owned\n")
        with self.assertRaisesRegex(ManagedSectionError, "content drifted"):
            prepare_managed_update(marked.replace("owned", "user edit"), "index", "new\n")

    def test_identical_content_does_not_rewrite_index(self):
        update_index = load_update_index()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "index.md"
            path.write_text(render_managed_section("index", "same\n"), encoding="utf-8")
            before = path.stat().st_mtime_ns
            time.sleep(0.01)

            changed = update_index.write_index_safely(path, "same\n")

            self.assertFalse(changed)
            self.assertEqual(path.stat().st_mtime_ns, before)

    def test_new_index_is_marked_and_atomic_writer_reports_change(self):
        update_index = load_update_index()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "wiki" / "index.md"

            changed = update_index.write_index_safely(path, "generated\n")

            self.assertTrue(changed)
            self.assertEqual(parse_managed_section(path.read_text(), "index").body, "generated\n")


if __name__ == "__main__":
    unittest.main()
