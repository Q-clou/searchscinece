# -*- coding: utf-8 -*-
# PubMed / PubMed Central search module for SearchScience v5.0
# Uses NCBI Entrez API query templates and Agent web_search.
import re, logging
from datetime import datetime, timedelta
from urllib.parse import quote

logger = logging.getLogger(__name__)

PUBMED_BASE = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils'

def build_pubmed_queries(keywords_en, days=365):
    queries = []
    start = (datetime.now() - timedelta(days=days)).strftime('%Y/%m/%d')
    end = datetime.now().strftime('%Y/%m/%d')
    for kw_group in keywords_en[:5]:
        kw_str = ' '.join(kw_group if isinstance(kw_group, list) else [kw_group])
        queries.append(('site:pubmed.ncbi.nlm.nih.gov ' + kw_str, 'PubMed: ' + kw_str[:40]))
    remote_sensing_queries = [
        'remote sensing semantic segmentation deep learning',
        'point cloud LiDAR 3D reconstruction',
        'UAV photogrammetry SLAM',
        'hyperspectral image classification',
        'InSAR deformation monitoring',
        'change detection remote sensing multi-temporal',
        'Gaussian splatting 3D reconstruction NeRF',
    ]
    for q in remote_sensing_queries:
        queries.append(('site:pubmed.ncbi.nlm.nih.gov ' + q, 'PubMed-RS: ' + q[:40]))
    return queries

def parse_pubmed_results(text):
    papers = []
    import re as _re
    pattern = _re.compile(
        r'(?P<title>[^\n]{15,200}?)\s*\.\s*'
        r'(?P<authors>[^\n]{10,150}?)\s*\.\s*'
        r'(?P<journal>[A-Z][^\n]{8,100}?)\s*\.\s*'
        r'(?P<date>\d{4})',
        _re.MULTILINE
    )
    for m in pattern.finditer(text):
        title = m.group('title').strip()
        if len(title) < 10:
            continue
        papers.append(dict(
            title=title,
            authors=[a.strip().rstrip('.') for a in m.group('authors').split(',')[:8]],
            venue=m.group('journal').strip(),
            published=m.group('date'),
            source='pubmed',
            language='en',
        ))
    return papers
