# -*- coding: utf-8 -*-
# CNKI search module for SearchScience v5.0
# Provides structured query building and result parsing for CNKI.
# Primary method: Codex Agent web_search with query templates.
import re, json, logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

CNKI_JOURNALS = dict(
    top=['测绘学报', '遥感学报', '武汉大学学报信息科学版'],
    remote_sensing=['遥感技术与应用', '国土资源遥感', '遥感信息'],
    surveying=['测绘科学', '测绘通报', '测绘工程'],
    gis=['地球信息科学学报', '地理与地理信息科学'],
)

def build_cnki_queries(keywords_cn, days=365):
    queries = []
    for kw in keywords_cn[:6]:
        queries.append((f'site:cnki.net {kw} 2025 2026', f'CNKI关键词: {kw}'))
    for journal in CNKI_JOURNALS.get('top', []):
        for kw in keywords_cn[:2]:
            queries.append((f'site:cnki.net {kw} {journal}', f'CNKI: {kw} @ {journal}'))
    direction_combos = [
        '遥感 语义分割 深度学习',
        '点云 LiDAR 语义分割 实例分割',
        '无人机 倾斜摄影 三维重建',
        'LiDAR SLAM 多传感器融合',
        '高光谱 分类 降维 波段选择',
        'InSAR 形变监测 DInSAR SBAS',
        '遥感 变化检测 多时相',
        '三维重建 NeRF 高斯泼溅 Gaussian Splatting',
    ]
    for combo in direction_combos:
        queries.append((f'site:cnki.net {combo} 2024 2025 2026', f'CNKI方向: {combo[:30]}'))
    return queries

def parse_cnki_results(text):
    papers = []
    import re as _re
    p = _re.compile(r'(?P<title>[^\n]{10,200}?)\n(?P<authors>[^\n]{5,80}?)\n(?P<journal>[^\n]{4,60}?),?\s*(?P<date>\d{4})')
    for m in p.finditer(text):
        title = m.group('title').strip()
        if len(title) < 8 or any(s in title for s in ['征稿','通知','启事','会议']):
            continue
        papers.append(dict(
            title=title,
            authors=[a.strip() for a in m.group('authors').replace(',','，').split('，') if a.strip()],
            venue=m.group('journal').strip(),
            published=m.group('date').strip(),
            source='cnki',
            language='zh',
        ))
    return papers

def dedup_cnki(papers):
    seen = set()
    result = []
    for p in papers:
        k = p.get('title','')[:30].lower().replace(' ','')
        if k and k not in seen:
            seen.add(k)
            result.append(p)
    return result
