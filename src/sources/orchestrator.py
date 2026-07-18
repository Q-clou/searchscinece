# Multi-source orchestrator v5.0 - SearchScience
import json, os, logging, subprocess, sys
from datetime import datetime

logger = logging.getLogger(__name__)

class SourceStatus:
    PENDING = 'pending'
    RUNNING = 'running'
    SUCCESS = 'success'
    FAILED = 'failed'
    SKIPPED = 'skipped'

class MultiSourceOrchestrator:
    def __init__(self, profile, output_dir, max_workers=3):
        self.profile = profile
        self.output_dir = output_dir
        self.max_workers = max_workers
        self.results = {}
        self.errors = {}
        self.stats = {'total': 0, 'dedup_removed': 0, 'by_source': {}}

    def search_arxiv(self, src_cfg):
        try:
            skill_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            script = os.path.join(skill_dir, 'scripts', 'fetch_papers.py')
            out_file = os.path.join(self.output_dir, 'papers_arxiv.json')
            max_res = min(src_cfg.get('max_papers_per_query', 3) * 3, 15)
            r = subprocess.run(
                [sys.executable, script, '--output', out_file,
                 '--max-results', str(max_res),
                 '--profile-path', self.profile.path or ''],
                capture_output=True, text=True, timeout=180)
            if os.path.exists(out_file):
                with open(out_file, 'r', encoding='utf-8') as f:
                    papers = json.load(f)
                return papers, SourceStatus.SUCCESS
            return [], SourceStatus.PARTIAL
        except Exception as e:
            logger.warning(f'ArXiv search error: {e}')
            return [], SourceStatus.FAILED

    def get_summary(self):
        lines = ['=== Multi-Source Summary ===']
        lines.append('Total papers: ' + str(self.stats.get('total', 0)))
        for src, status in self.results.items():
            cnt = self.stats.get('by_source', {}).get(src, 0)
            ok = 'OK' if status == SourceStatus.SUCCESS else 'FAIL'
            lines.append('  [' + ok + '] ' + src + ': ' + str(cnt) + ' papers')
        return chr(10).join(lines)
