# Unit tests
import json, os, sys, unittest, tempfile
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SKILL_DIR)
from src.utils.config import validate_profile_data

class TestProfileValidation(unittest.TestCase):
    def test_valid(self):
        v = dict(user=dict(name='test'), research_directions=[dict(name='RS', keywords_cn=['a'], weight=8)], sources=dict(arxiv=dict(enabled=True)), exclude_keywords=[])
        ok, errs = validate_profile_data(v)
        self.assertTrue(ok, msg=str(errs))

    def test_missing(self):
        ok, errs = validate_profile_data(dict())
        self.assertFalse(ok)

class TestTracker(unittest.TestCase):
    def setUp(self):
        from src.utils.progress import ProgressTracker
        self.td = tempfile.mkdtemp()
        self.tr = ProgressTracker(self.td, '2026-07-18')
    def tearDown(self):
        import shutil; shutil.rmtree(self.td, ignore_errors=True)
    def test_mark(self):
        self.tr.mark_completed('fetch', total_papers=10)
        self.assertTrue(self.tr.is_completed('fetch'))
    def test_pending(self):
        self.tr.mark_completed('fetch')
        self.assertEqual(self.tr.get_pending_steps(['fetch', 'report']), ['report'])

class TestDedup(unittest.TestCase):
    def test_dup(self):
        from src.utils.progress import dedup_papers
        r, n = dedup_papers([dict(title='A', arxiv_id='1234.5678'), dict(title='B', arxiv_id='1234.5678')])
        self.assertEqual(len(r), 1)

if __name__ == '__main__':
    unittest.main(verbosity=2)
