"""Tests for check_update.py. Run: python3 -I -m unittest discover -s <scripts dir> -p 'test_*.py'"""
import io
import json
import os
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_update as cu  # noqa: E402


class ParseVersion(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(cu.parse_version("0.3.0"), (0, 3, 0))

    def test_numeric_not_string_order(self):
        self.assertGreater(cu.parse_version("0.10.0"), cu.parse_version("0.9.0"))

    def test_bad(self):
        self.assertIsNone(cu.parse_version("abc"))
        self.assertIsNone(cu.parse_version(None))


class Status(unittest.TestCase):
    def test_behind(self):
        self.assertEqual(cu.status("0.3.0", "0.4.0"), "behind")

    def test_current(self):
        self.assertEqual(cu.status("0.3.0", "0.3.0"), "current")

    def test_ahead(self):  # e.g. a local --plugin-dir copy on a branch
        self.assertEqual(cu.status("0.4.0", "0.3.0"), "ahead")

    def test_unknown(self):
        self.assertEqual(cu.status("0.3.0", "garbage"), "unknown")


class Main(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cache = Path(self.tmp.name) / "update-check.json"
        self.calls = 0

    def tearDown(self):
        self.tmp.cleanup()

    def fetch(self, version):
        def _f():
            self.calls += 1
            if isinstance(version, Exception):
                raise version
            return version
        return _f

    def run_main(self, installed, fetch):
        out = io.StringIO()
        with redirect_stdout(out):
            rc = cu.run(installed, fetch, self.cache)
        return rc, out.getvalue()

    def test_behind_message(self):
        rc, out = self.run_main("0.3.0", self.fetch("0.4.0"))
        self.assertEqual(rc, 0)
        self.assertIn("UPDATE AVAILABLE", out)
        self.assertIn("0.3.0", out)
        self.assertIn("0.4.0", out)

    def test_current_message(self):
        rc, out = self.run_main("0.3.0", self.fetch("0.3.0"))
        self.assertEqual(rc, 0)
        self.assertIn("up to date", out)
        self.assertNotIn("UPDATE AVAILABLE", out)

    def test_network_error_is_quiet_and_exit_0(self):
        rc, out = self.run_main("0.3.0", self.fetch(OSError("no network")))
        self.assertEqual(rc, 0)
        self.assertIn("skipped", out)
        self.assertNotIn("UPDATE AVAILABLE", out)

    def test_cache_avoids_second_fetch(self):
        self.run_main("0.3.0", self.fetch("0.4.0"))
        rc, out = self.run_main("0.3.0", self.fetch("0.4.0"))
        self.assertEqual(self.calls, 1)
        self.assertIn("UPDATE AVAILABLE", out)

    def test_stale_cache_refetches(self):
        self.run_main("0.3.0", self.fetch("0.4.0"))
        old = time.time() - cu.CACHE_SECONDS - 10
        os.utime(self.cache, (old, old))
        self.run_main("0.3.0", self.fetch("0.4.0"))
        self.assertEqual(self.calls, 2)

    def test_corrupt_cache_refetches(self):
        self.cache.write_text("{not json")
        rc, out = self.run_main("0.3.0", self.fetch("0.3.0"))
        self.assertEqual(self.calls, 1)
        self.assertIn("up to date", out)

    def test_cache_written_as_json(self):
        self.run_main("0.3.0", self.fetch("0.4.0"))
        self.assertEqual(json.loads(self.cache.read_text())["latest"], "0.4.0")


class InstalledVersion(unittest.TestCase):
    def test_reads_this_plugins_manifest(self):
        manifest = Path(__file__).resolve().parents[3] / ".claude-plugin" / "plugin.json"
        self.assertEqual(cu.installed_version(), json.loads(manifest.read_text())["version"])


if __name__ == "__main__":
    unittest.main()
