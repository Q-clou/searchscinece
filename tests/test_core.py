
"""Unit tests for SearchScience core modules.

Usage: python -m pytest test_core.py -v
   or: python test_core.py
"""
import json, os, sys, unittest, tempfile

SKILL_DIR = os.path.expanduser(r"~\~.codex\skills\searchscinece")
SKILL_DIR = SKILL_DIR.replace("~\\~", "~\\")
SKILL_DIR = os.path.expanduser(r"~\.codex\skills\searchscinece")
sys.path.insert(0, SKILL_DIR)
from src.utils.config import validate_profile_data

# ---------------------------------------------------------------------------
# Test: Robust utilities (safe_text, retry, safe_write_json, safe_read_json)
# ---------------------------------------------------------------------------
class TestRobust(unittest.TestCase):
    def test_safe_text(self):
        from src.utils.progress import safe_text
        self.assertEqual(safe_text(None), "")
        self.assertEqual(safe_text("  hello  "), "hello")
        self.assertEqual(safe_text(42), "42")
        self.assertEqual(safe_text(True), "True")
        # Truncation
        self.assertEqual(len(safe_text("a" * 5000, max_len=100)), 100)

    def test_retry_success(self):
        from src.utils.progress import retry
        call_count = [0]
        @retry(max_attempts=3, delay=0.01)
        def succeed():
            call_count[0] += 1
            return "ok"
        self.assertEqual(succeed(), "ok")
        self.assertEqual(call_count[0], 1)

    def test_retry_eventual_failure(self):
        from src.utils.progress import retry
        @retry(max_attempts=2, delay=0.01)
        def always_fail():
            raise ValueError("test error")
        with self.assertRaises(ValueError):
            always_fail()

    def test_safe_write_read_json(self):
        from src.utils.progress import safe_write_json
        import json as jmod
        tmpdir = tempfile.gettempdir()
        fp = os.path.join(tmpdir, "test_ss.json")
        data = {"key": "value", "nested": {"a": 1}}
        self.assertTrue(safe_write_json(fp, data))
        with open(fp, "r", encoding="utf-8") as f:
            self.assertEqual(jmod.load(f), data)
        os.remove(fp)
        os.remove(fp + ".tmp") if os.path.exists(fp + ".tmp") else None

# ---------------------------------------------------------------------------
# Test: Profile validation
# ---------------------------------------------------------------------------
class TestProfileValidation(unittest.TestCase):
    def test_valid_profile(self):
        valid = {
            "user": {"name": "test", "language_preference": "zh"},
            "research_directions": [
                {"name": "RS", "keywords_cn": ["remote sensing"], "keywords_en": ["rs"], "weight": 8}
            ],
            "sources": {"arxiv": {"enabled": True}, "cnki": {"enabled": False}},
            "exclude_keywords": []
        }
        ok, errs = validate_profile_data(valid)
        self.assertTrue(ok, msg=f"Expected valid, got errors: {errs}")

    def test_missing_required(self):
        ok, errs = validate_profile_data({})
        self.assertFalse(ok)
        self.assertTrue(any("Missing" in e for e in errs))

    def test_invalid_weight(self):
        bad = {
            "user": {"name": "x", "language_preference": "zh"},
            "research_directions": [{"name": "X", "keywords_cn": ["a"], "weight": 99}],
            "sources": {"arxiv": {"enabled": True}},
            "exclude_keywords": []
        }
        ok, errs = validate_profile_data(bad)
        self.assertFalse(ok)
        self.assertTrue(any("weight" in e for e in errs))

    def test_invalid_language(self):
        bad = {
            "user": {"name": "x", "language_preference": "fr"},
            "research_directions": [{"name": "X", "keywords_cn": ["a"], "weight": 5}],
            "sources": {"arxiv": {"enabled": True}},
            "exclude_keywords": []
        }
        ok, errs = validate_profile_data(bad)
        self.assertFalse(ok)
        self.assertTrue(any("language" in e.lower() for e in errs))

    def test_no_sources_enabled(self):
        bad = {
            "user": {"name": "x", "language_preference": "zh"},
            "research_directions": [{"name": "X", "keywords_cn": ["a"], "weight": 5}],
            "sources": {},
            "exclude_keywords": []
        }
        ok, errs = validate_profile_data(bad)
        self.assertFalse(ok)
        self.assertTrue(any("source" in e.lower() for e in errs))

# ---------------------------------------------------------------------------
# Test: Progress tracker
# ---------------------------------------------------------------------------
class TestProgressTracker(unittest.TestCase):
    def setUp(self):
        from src.utils.progress import ProgressTracker
        self.tmpdir = tempfile.mkdtemp()
        self.tracker = ProgressTracker(self.tmpdir, "2026-07-18")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init_creates_default(self):
        self.assertEqual(self.tracker.date_str, "2026-07-18")
        self.assertFalse(self.tracker.is_completed("fetch"))

    def test_mark_completed(self):
        self.tracker.mark_completed("fetch", total_papers=10)
        self.assertTrue(self.tracker.is_completed("fetch"))
        self.assertEqual(self.tracker.data["stats"]["total_papers"], 10)

    def test_get_pending(self):
        all_steps = ["fetch", "analyze", "report"]
        self.tracker.mark_completed("fetch")
        pending = self.tracker.get_pending_steps(all_steps)
        self.assertEqual(pending, ["analyze", "report"])

    def test_reset_step(self):
        self.tracker.mark_completed("fetch")
        self.tracker.reset_step("fetch")
        self.assertFalse(self.tracker.is_completed("fetch"))

    def test_resume_persistence(self):
        self.tracker.mark_completed("fetch")
        self.tracker.save()
        # Create a new tracker pointing to same dir
        from src.utils.progress import ProgressTracker
        t2 = ProgressTracker(self.tmpdir, "2026-07-18")
        self.assertTrue(t2.is_completed("fetch"))

# ---------------------------------------------------------------------------
# Test: PDF builders (import only - reportlab rendering tested separately)
# ---------------------------------------------------------------------------
class TestBuilders(unittest.TestCase):
    def test_import_builders(self):
        from scripts.v3_builders import V3_BUILDERS, safe_build, T
        self.assertEqual(len(V3_BUILDERS), 11)
        self.assertTrue(callable(safe_build))

    def test_builder_no_crash_empty_data(self):
        from scripts.v3_builders import safe_build, sec_km, sec_pa
        # Empty data should not raise
        result = safe_build(sec_km, {}, {})
        self.assertEqual(result, [])
        result = safe_build(sec_pa, None, {})
        self.assertEqual(result, [])

    def test_T_function(self):
        from scripts.v3_builders import T
        self.assertEqual(T(None), "")
        self.assertEqual(T("  hello  "), "hello")
        self.assertEqual(T(42), "42")

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    unittest.main(verbosity=2)
